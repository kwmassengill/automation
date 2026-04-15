#!/usr/bin/env python3
"""
Script 2: Airtable New Prospect → Send Qualification Email (with Google OAuth)

SAFEGUARDS:
- DRY_RUN mode (set to False after verification)
- MAX_EMAILS_PER_RUN = 1 (prevent mass mailings)
- Filter validation (Email exists AND In Automation = TRUE AND Qualification Status = New)
- Email format validation
- State tracking (prevents duplicate sends)

FIELDS UPDATED ON EMAIL SEND:
- Qualification Email Sent (timestamp)
- Qualification Status → "Qualification Email Sent"
- Deal Phase → "Initial Contact — Awaiting response"
- Deal Phase Date → current date
- Priority → "Watch — Strategic monitor, no active pursuit"
"""

import os
import sys
import json
import time
import sqlite3
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from email.mime.text import MIMEText

# Load .env file first
from dotenv import load_dotenv
load_dotenv(Path.home() / "Automations/config/.env")

# Third-party imports
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ============================================================================
# SAFEGUARD SETTINGS
# ============================================================================
DRY_RUN = False  # Set to True for testing without sending emails
MAX_EMAILS_PER_RUN = 1  # Maximum emails to send per execution
# ============================================================================

# Configuration
SCRIPT_NAME = "script_02_airtable_qualification_email"
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = "appoNkgoKHAUXgXV9"
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"

# Airtable Field IDs
FIELD_TIMESTAMP = "fldI2tIVJyDy1Cymi"
FIELD_STATUS = "fldgCH6CyIsNUCkV8"
FIELD_DEAL_PHASE = "fld07a0yFNwo92lTs"
FIELD_DEAL_PHASE_DATE = "fldNZDQaLsGJoQQhn"
FIELD_PRIORITY = "fld5E4Nud5bAg0hXb"

# Paths
HOME = Path.home()
LOG_DIR = HOME / "Automations" / "logs"
CONFIG_DIR = HOME / "Automations" / "config"
STATE_DB = CONFIG_DIR / "state.db"
OAUTH_CREDENTIALS_FILE = CONFIG_DIR / "oauth_credentials.json"
OAUTH_TOKEN_FILE = CONFIG_DIR / "google_token.json"  # Shared token file used by all scripts

# Create directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Gmail API scopes - must match scopes in google_token.json
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/calendar"]

# Logging setup
def setup_logger( ):
    """Configure logging."""
    import logging
    logger = logging.getLogger(SCRIPT_NAME)
    logger.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler(LOG_DIR / f"{SCRIPT_NAME}.log")
    fh.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()

# Log safeguard settings
logger.info(f"SAFEGUARD SETTINGS: DRY_RUN={DRY_RUN}, MAX_EMAILS_PER_RUN={MAX_EMAILS_PER_RUN}")

# State management
class StateManager:
    """Manage script state in SQLite."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_records (
                record_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def is_processed(self, record_id: str) -> bool:
        """Check if record has been processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM processed_records WHERE record_id = ?', (record_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def mark_processed(self, record_id: str, status: str = "success"):
        """Mark record as processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO processed_records (record_id, processed_at, status) VALUES (?, ?, ?)',
            (record_id, datetime.now().isoformat(), status)
        )
        conn.commit()
        conn.close()

state_manager = StateManager(STATE_DB)

# Google OAuth setup
def get_gmail_service():
    """Get authenticated Gmail service using OAuth."""
    creds = None
    
    if OAUTH_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), GMAIL_SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(OAUTH_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            logger.info("OAuth token refreshed successfully")
        else:
            logger.error(f"OAuth token invalid and cannot be refreshed. Please re-authorize.")
            raise RuntimeError("OAuth token requires re-authorization")
        
        with open(OAUTH_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

# Airtable client
class AirtableClient:
    """Airtable API client."""
    
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_new_prospects(self, table_id: str ) -> List[Dict[str, Any]]:
        """Get prospects matching filter: Email exists AND In Automation = true AND Qualification Status = New."""
        # Filter: Has Email AND In Automation = TRUE AND Qualification Status = "New"
        filter_formula = "AND(NOT({Email} = BLANK()), {In Automation} = 1, {Qualification Status} = 'New')"
        
        url = f"{self.base_url}/{self.base_id}/{table_id}"
        params = {
            "filterByFormula": filter_formula,
            "maxRecords": 100
        }
        
        logger.debug(f"Filter formula: {filter_formula}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            records = response.json().get("records", [])
            logger.info(f"Airtable filter returned {len(records)} records")
            
            # SAFEGUARD: Warn if more than 10 records (unusual)
            if len(records) > 10:
                logger.warning(f"SAFEGUARD ALERT: Found {len(records)} prospects (unusual). Check filter.")
            
            return records
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Airtable records: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def update_record_status(self, table_id: str, record_id: str):
        """Update Airtable record with email sent status and deal phase info."""
        url = f"{self.base_url}/{self.base_id}/{table_id}/{record_id}"
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        data = {
            "fields": {
                FIELD_TIMESTAMP: datetime.now().isoformat(),
                FIELD_STATUS: "Qualification Email Sent",
                FIELD_DEAL_PHASE: "Initial Contact — Awaiting response",
                FIELD_DEAL_PHASE_DATE: today,
                FIELD_PRIORITY: "Watch — Strategic monitor, no active pursuit"
            }
        }
        
        try:
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            logger.info(f"Updated Airtable record {record_id} with all fields")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating Airtable record {record_id}: {str(e)}")
            raise

# Email validation
def is_valid_email(email: str) -> bool:
    """Validate email format."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Email template
def get_email_template(prospect: Dict[str, Any]) -> tuple:
    """Get personalized email subject and body."""
    fields = prospect.get("fields", {})
    first_name = fields.get("First Name", "there")
    
    subject = f"Two Quick Questions About {fields.get('Company', 'Your Company')} Before We Meet"
    
    # Clean, simple HTML format that renders well in Gmail
    body = f"""<html>
<body style="font-family: 'Times New Roman', Times, serif; font-size: 14px; line-height: 1.6; color: #333;">

<p>Hi {first_name},</p>

<p>Great to hear from you. Before we schedule time together, I want to make sure we're a good fit.</p>

<p>Here is a 5-minute video that quickly explains our offer:</p>

<div style="margin: 20px 0;">
  <a href="https://youtu.be/L0WIPiMFtRs" style="display: inline-block; padding: 12px 24px; background-color: #C9A84C; color: #1A1A1A; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 15px; font-family: 'Times New Roman', Times, serif;">▶ Watch the 5-Minute Overview</a>
</div>

<p>If that sounds interesting, I have two quick questions:</p>

<p>1. What's your approximate annual EBITDA? (Ranges are fine: &lt;$500K, $500K-$2M, $2M-$5M, $5M+ )</p>

<p>2. Would you be open to a structured 10-year payout if it meant a significantly higher sale price and better tax treatment—or do you need maximum cash at closing?</p>

<p>Your honest answers save us both time. If our model doesn't fit, I'm happy to connect you with excellent traditional brokers.</p>

<p>Looking forward to your response, {first_name}.</p>

<p>Cordially,</p>

<p style="margin: 0; padding: 0; font-family: 'Times New Roman', Times, serif;">Kevin Massengill</p>
<p style="margin: 0; padding: 0; font-family: 'Times New Roman', Times, serif;">Chairman &amp; CEO</p>
<p style="margin: 0; padding: 0; font-family: 'Times New Roman', Times, serif;">Meraglim Holdings Corporation</p>
<p style="margin: 0; padding: 0; font-family: 'Times New Roman', Times, serif;"><a href="mailto:kmassengill@meraglim.com">kmassengill@meraglim.com</a></p>

</body>
</html>"""
    
    return subject, body

# Send email via Gmail
def send_email(service, to_email: str, subject: str, body: str, dry_run: bool = False) -> bool:
    """Send email via Gmail API."""
    try:
        if dry_run:
            logger.info(f"DRY RUN: Would send email to {to_email} with subject: {subject}")
            return True
        
        message = MIMEText(body, 'html')
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = 'kmassengill@meraglim.com'
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        send_message = {'raw': raw_message}
        service.users().messages().send(userId='me', body=send_message).execute()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False

# Main function
def main():
    """Main script logic."""
    logger.info(f"Starting {SCRIPT_NAME}")
    
    if not AIRTABLE_API_KEY:
        logger.error("AIRTABLE_API_KEY not found in environment")
        return
    
    try:
        airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
        gmail_service = get_gmail_service()
        
        logger.info("Fetching new prospects from Airtable...")
        prospects = airtable.get_new_prospects(AIRTABLE_TABLE_ID)
        logger.info(f"Found {len(prospects)} prospects matching filter")
        
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for prospect in prospects:
            # SAFEGUARD: Stop if we've reached max emails per run
            if processed_count >= MAX_EMAILS_PER_RUN:
                logger.info(f"Reached max emails per run ({MAX_EMAILS_PER_RUN}). Stopping.")
                break
            
            record_id = prospect.get("id")
            fields = prospect.get("fields", {})
            email = fields.get("Email")
            
            if state_manager.is_processed(record_id):
                logger.debug(f"Skipping already processed record: {record_id}")
                skipped_count += 1
                continue
            
            if not email:
                logger.warning(f"No email for prospect {record_id}")
                state_manager.mark_processed(record_id, "skipped_no_email")
                skipped_count += 1
                continue
            
            # SAFEGUARD: Validate email format
            if not is_valid_email(email):
                logger.warning(f"Invalid email format: {email} for record {record_id}")
                state_manager.mark_processed(record_id, "skipped_invalid_email")
                skipped_count += 1
                continue
            
            try:
                subject, body = get_email_template(prospect)
                
                if send_email(gmail_service, email, subject, body, dry_run=DRY_RUN):
                    if not DRY_RUN:
                        airtable.update_record_status(AIRTABLE_TABLE_ID, record_id)
                    state_manager.mark_processed(record_id, "success")
                    processed_count += 1
                    time.sleep(1)
                else:
                    error_count += 1
                    state_manager.mark_processed(record_id, "error")
                    
            except Exception as e:
                logger.error(f"Error processing prospect {record_id}: {str(e)}")
                error_count += 1
                state_manager.mark_processed(record_id, "error")
        
        logger.info(f"Completed: {processed_count} sent, {skipped_count} skipped, {error_count} errors")
        if DRY_RUN:
            logger.info("DRY RUN MODE - No emails were actually sent")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
