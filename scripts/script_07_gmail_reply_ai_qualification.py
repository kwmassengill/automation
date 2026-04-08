#!/usr/bin/env python3
"""
Script 7: Gmail Reply → AI Qualification
Monitors Gmail for prospect replies, analyzes them with Claude AI,
and updates Airtable with qualification status.
"""

import os
import sys
import json
import time
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Third-party imports
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from email.utils import parseaddr

# Load environment variables
# First try to load from the current directory (for testing in deployment folder)
from pathlib import Path
env_path = Path(__file__).parent.parent / 'config' / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fall back to default location
    load_dotenv()

# Configuration
AUTOMATION_BASE_PATH = os.getenv("AUTOMATION_BASE_PATH", "/Users/kevinmassengill/Automations")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("true", "1", "t")
MAX_EMAILS_PER_RUN = int(os.getenv("MAX_EMAILS_PER_RUN", "10"))

# API Keys & Tokens
GMAIL_QUERY = os.getenv("GMAIL_QUERY", "is:unread")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", f"{AUTOMATION_BASE_PATH}/config/google_token.json")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_ID = os.getenv("AIRTABLE_TABLE_ID")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

# Setup Logging
log_dir = Path(AUTOMATION_BASE_PATH) / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"script_07_gmail_reply_ai_qualification_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Setup State Database
db_path = Path(AUTOMATION_BASE_PATH) / "config" / "state.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """Initialize the SQLite database for tracking processed emails."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            email_message_id TEXT PRIMARY KEY,
            prospect_airtable_id TEXT,
            sender_email TEXT,
            processed_date TEXT,
            qualification_decision TEXT,
            ai_analysis TEXT
        )
    ''')
    conn.commit()
    return conn

def is_email_processed(conn, message_id: str) -> bool:
    """Check if an email has already been processed."""
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM processed_emails WHERE email_message_id = ?', (message_id,))
    return cursor.fetchone() is not None

def mark_email_processed(conn, message_id: str, prospect_id: str, sender_email: str, decision: str, analysis: str):
    """Record an email as processed in the database."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would mark email {message_id} as processed in DB")
        return
        
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO processed_emails 
        (email_message_id, prospect_airtable_id, sender_email, processed_date, qualification_decision, ai_analysis)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (message_id, prospect_id, sender_email, datetime.now().isoformat(), decision, analysis))
    conn.commit()

def get_gmail_service():
    """Authenticate and return the Gmail API service."""
    if not os.path.exists(GOOGLE_TOKEN_FILE):
        logger.error(f"Google token file not found at {GOOGLE_TOKEN_FILE}")
        return None
        
    try:
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, ['https://www.googleapis.com/auth/gmail.modify'])
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to initialize Gmail service: {e}")
        return None

def get_unread_emails(service) -> List[Dict]:
    """Fetch unread emails matching the query."""
    try:
        results = service.users().messages().list(userId='me', q=GMAIL_QUERY, maxResults=MAX_EMAILS_PER_RUN).execute()
        messages = results.get('messages', [])
        
        if not messages:
            logger.info("No unread emails found.")
            return []
            
        email_details = []
        for msg in messages:
            msg_id = msg['id']
            # Get full message details
            message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            
            # Parse sender email
            _, sender_email = parseaddr(from_header)
            
            # Apply Filter 1: "Only Prospect Replies"
            # Subject must contain "Re:" and From must not contain "@meraglim.com"
            if "re:" not in subject.lower():
                logger.debug(f"Skipping email {msg_id}: Subject does not contain 'Re:'")
                continue
                
            if "@meraglim.com" in sender_email.lower():
                logger.debug(f"Skipping email {msg_id}: Sender is internal (@meraglim.com)")
                continue
                
            # Extract body (snippet is usually enough for AI, but we can get full body if needed)
            snippet = message.get('snippet', '')
            
            email_details.append({
                'id': msg_id,
                'threadId': message['threadId'],
                'subject': subject,
                'sender_email': sender_email,
                'snippet': snippet
            })
            
        return email_details
    except HttpError as error:
        logger.error(f"An error occurred fetching emails: {error}")
        return []

def find_prospect_in_airtable(sender_email: str) -> Optional[Dict]:
    """Search Airtable for a prospect matching the sender email."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Case-insensitive email match
    formula = f"LOWER({{Email}}) = LOWER('{sender_email}')"
    params = {
        "filterByFormula": formula,
        "maxRecords": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('records', [])
        if not records:
            return None
            
        return records[0]
    except Exception as e:
        logger.error(f"Error searching Airtable for {sender_email}: {e}")
        return None

def analyze_email_with_claude(email_snippet: str) -> Dict:
    """Send email snippet to Claude for qualification analysis."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Return ONLY raw valid JSON with no markdown, no code blocks, no backticks, no ```json wrapper. 
Use these EXACT values:
- ebitda_range must be one of: <$500K, $500K-$2M, $2M-$5M, $5M-$10M, $10M+, Unknown. 
- qualification_decision must be one of: Qualified, Not Qualified, Needs Review. 
- payment_willingness must be one of: Structured Payments Preferred, Cash Only Required, Open to Either, Unknown. 
- notes: 2-3 sentence summary. 

Email: {email_snippet}"""

    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 800,
        "temperature": float(os.getenv("CLAUDE_TEMPERATURE", "0.3")),
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result_text = response.json()['content'][0]['text']
        
        # Clean up potential markdown formatting if Claude ignored instructions
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        return json.loads(result_text.strip())
    except Exception as e:
        logger.error(f"Error analyzing email with Claude: {e}")
        if 'response' in locals():
            logger.error(f"Claude API Response: {response.text}")
        return {
            "qualification_decision": "Needs Review",
            "notes": f"Error during AI analysis: {str(e)}",
            "ebitda_range": "Unknown",
            "payment_willingness": "Unknown"
        }

def update_airtable_record(record_id: str, analysis_result: Dict) -> bool:
    """Update the prospect record in Airtable with AI analysis results."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Map JSON fields to Airtable fields based on blueprint
    fields = {
        "fld3rnYxi5f20dQMN": analysis_result.get("ebitda_range", "Unknown"), # EBITDA Range
        "fldArNm1cnJ1zaO8O": True, # In Automation
        "fldDyXzREoz4VeBCP": analysis_result.get("payment_willingness", "Unknown"), # Payment Willingness
        "fldGQ75eBvez8yQuT": analysis_result.get("notes", ""), # Notes
        "fldgCH6CyIsNUCkV8": analysis_result.get("qualification_decision", "Needs Review") # Qualification Decision
    }
    
    # Update Deal Phase based on qualification decision
    qualification_decision = analysis_result.get("qualification_decision", "Needs Review")
    if qualification_decision == "Qualified":
        fields["fld07a0yFNwo92lTs"] = "Pre-Qualification — Actively assessing against ABB criteria" # Deal Phase
    elif qualification_decision == "Not Qualified":
        fields["fld07a0yFNwo92lTs"] = "Disqualified — No fit or no budget" # Deal Phase
    
    payload = {
        "fields": fields,
        "typecast": True
    }
    
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would update Airtable record {record_id} with: {json.dumps(fields, indent=2)}")
        return True
        
    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully updated Airtable record {record_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating Airtable record {record_id}: {e}")
        if 'response' in locals():
            logger.error(f"Airtable API Response: {response.text}")
        return False

def mark_email_as_read(service, message_id: str) -> bool:
    """Remove the UNREAD label from the email."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would mark email {message_id} as read")
        return True
        
    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        logger.info(f"Marked email {message_id} as read")
        return True
    except Exception as e:
        logger.error(f"Error marking email {message_id} as read: {e}")
        return False

def main():
    logger.info(f"Starting Script 7: Gmail Reply → AI Qualification (DRY_RUN={DRY_RUN})")
    
    # Initialize DB
    conn = init_db()
    
    # Get Gmail Service
    gmail_service = get_gmail_service()
    if not gmail_service:
        logger.error("Could not initialize Gmail service. Exiting.")
        return
        
    # Get unread emails matching criteria
    emails = get_unread_emails(gmail_service)
    logger.info(f"Found {len(emails)} potential prospect replies to process.")
    
    processed_count = 0
    
    for email_data in emails:
        msg_id = email_data['id']
        sender_email = email_data['sender_email']
        
        # Check if already processed
        if is_email_processed(conn, msg_id):
            logger.info(f"Email {msg_id} already processed. Skipping.")
            # Ensure it's marked as read just in case
            mark_email_as_read(gmail_service, msg_id)
            continue
            
        logger.info(f"Processing email from {sender_email} (Subject: {email_data['subject']})")
        
        # Filter 2: "Only If Prospect Found"
        prospect = find_prospect_in_airtable(sender_email)
        if not prospect:
            logger.warning(f"No prospect found in Airtable for email {sender_email}. Skipping.")
            # We don't mark as read here, maybe it needs manual review
            continue
            
        prospect_id = prospect['id']
        logger.info(f"Found prospect in Airtable: {prospect_id}")
        
        # Analyze with Claude
        logger.info("Analyzing email content with Claude AI...")
        analysis_result = analyze_email_with_claude(email_data['snippet'])
        logger.info(f"AI Decision: {analysis_result.get('qualification_decision')}")
        
        # Update Airtable
        success = update_airtable_record(prospect_id, analysis_result)
        
        if success:
            # Mark email as read
            mark_email_as_read(gmail_service, msg_id)
            
            # Record in state DB
            mark_email_processed(
                conn, 
                msg_id, 
                prospect_id, 
                sender_email, 
                analysis_result.get('qualification_decision', 'Unknown'),
                json.dumps(analysis_result)
            )
            processed_count += 1
            
    logger.info(f"Script 7 completed. Processed {processed_count} emails.")

if __name__ == "__main__":
    main()
