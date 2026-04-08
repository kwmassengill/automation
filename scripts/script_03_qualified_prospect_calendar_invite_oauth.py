#!/usr/bin/env python3
"""
Script 3: Qualified Prospect - Calendar Invite

SAFEGUARDS:
- DRY_RUN mode (set to False after verification)
- MAX_EMAILS_PER_RUN = 1 (prevent mass operations)
- Email validation
- State tracking (prevents duplicates)
"""

import os
import sys
import json
import time
import sqlite3
import re
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load .env file first
env_file = Path.home() / "Automations" / "config" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Add project root to path for shared_utils
sys.path.insert(0, str(Path.home() / "Automations" / "scripts"))
try:
    from shared_utils import setup_logger, StateManager, handle_errors
except ImportError:
    # Fallback if shared_utils is not in scripts dir
    sys.path.insert(0, str(Path.home() / "Automations" / "project_files"))
    from shared_utils import setup_logger, StateManager, handle_errors

# Third-party imports
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ============================================================================
# SAFEGUARD SETTINGS
# ============================================================================
DRY_RUN = False  # Set to True for testing
MAX_EMAILS_PER_RUN = 1  # Prevent mass operations

# ============================================================================
# CONFIGURATION
# ============================================================================
SCRIPT_NAME = "script_03_qualified_prospect_calendar_invite"
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = "appoNkgoKHAUXgXV9"
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"

# Paths
CONFIG_DIR = Path.home() / "Automations" / "config"
STATE_DB_PATH = CONFIG_DIR / "state.db"
GMAIL_TOKEN_FILE = CONFIG_DIR / "oauth_token.json"
GMAIL_CREDS_FILE = CONFIG_DIR / "oauth_credentials.json"

# Gmail Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# ============================================================================
# LOGGING & STATE
# ============================================================================
logger = setup_logger(SCRIPT_NAME)
state_manager = StateManager(str(STATE_DB_PATH))

# ============================================================================
# EMAIL TEMPLATE
# ============================================================================
def get_email_subject(company_name: str) -> str:
    return f"Let's schedule time - {company_name}"

def get_email_body(first_name: str, company_name: str) -> str:
    """
    Generate the HTML email body with proper formatting for Gmail.
    Uses <p> tags instead of <br> for reliable rendering.
    """
    return f"""
    <div style="font-family: 'Times New Roman', Times, serif; font-size: 14px; color: #000000;">
        <p style="margin: 0 0 15px 0;">Hi {first_name},</p>
        
        <p style="margin: 0 0 15px 0;">Thanks for confirming your interest and providing those details. Based on what you've shared, I think there's a strong fit for our Annuity Sale model.</p>
        
        <p style="margin: 0 0 15px 0;">Here's what makes sense as next steps:</p>
        
        <p style="margin: 0 0 15px 0;">
        1. 30-minute introductory call to discuss your specific situation<br>
        2. I'll share how our 10-year payment structure works and the tax advantages<br>
        3. We'll determine if this approach aligns with your exit timeline and goals
        </p>
        
        <p style="margin: 0 0 15px 0;">You can grab time directly on my calendar here:<br>
        <a href="https://meetings.hubspot.com/kmassengill" style="color: #1155cc;">https://meetings.hubspot.com/kmassengill</a></p>
        
        <p style="margin: 0 0 15px 0;">I'm looking forward to learning more about {company_name} and seeing if we can help you achieve a successful exit.</p>
        
        <p style="margin: 0 0 15px 0;">Cordially,</p>
        
        <p style="margin: 0; padding: 0;">Kevin Massengill</p>
        <p style="margin: 0; padding: 0;">Chairman & CEO</p>
        <p style="margin: 0; padding: 0;">Meraglim Holdings Corporation</p>
        <p style="margin: 0; padding: 0;"><a href="mailto:kmassengill@meraglim.com" style="color: #1155cc;">kmassengill@meraglim.com</a></p>
    </div>
    """

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = None
    
    if GMAIL_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Gmail token")
            creds.refresh(Request())
        else:
            if not GMAIL_CREDS_FILE.exists():
                raise FileNotFoundError(f"Gmail credentials file not found at {GMAIL_CREDS_FILE}")
            
            logger.info("Starting new Gmail OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(str(GMAIL_CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

def send_email(service, to_email: str, subject: str, html_body: str) -> bool:
    """Send an email using Gmail API."""
    try:
        message = MIMEMultipart('alternative')
        message['to'] = to_email
        message['subject'] = subject
        
        msg_body = MIMEText(html_body, 'html')
        message.attach(msg_body)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would send email to {to_email}")
            logger.debug(f"[DRY RUN] Subject: {subject}")
            return True
            
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        logger.info(f"Successfully sent email to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def get_qualified_prospects() -> List[Dict]:
    """Fetch qualified prospects from Airtable."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    }
    
    # Filter: Qualification Status = 'Qualified' AND Email is not blank AND In Automation = TRUE
    filter_formula = "AND({Qualification Status} = 'Qualified', NOT({Email} = BLANK()), {In Automation} = TRUE())"
    
    params = {
        "filterByFormula": filter_formula,
        "maxRecords": 10,
        "sort[0][field]": "Last Modified",
        "sort[0][direction]": "desc"
    }
    
    logger.info(f"Fetching prospects with formula: {filter_formula}")
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    records = response.json().get("records", [])
    logger.info(f"Found {len(records)} prospects matching criteria")
    return records

def update_airtable_record(record_id: str) -> bool:
    """Update Airtable record after sending email."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Fields to update
    # fldI2tIVJyDy1Cymi = Date Sent
    # fldgCH6CyIsNUCkV8 = Qualification Status
    
    current_time = datetime.utcnow().isoformat() + "Z"
    
    payload = {
        "fields": {
            "fldI2tIVJyDy1Cymi": current_time,
            "fldgCH6CyIsNUCkV8": "Meeting Invite Sent"
        }
    }
    
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would update record {record_id} with: {json.dumps(payload)}")
        return True
        
    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully updated Airtable record {record_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update Airtable record {record_id}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False

# ============================================================================
# MAIN LOGIC
# ============================================================================
@handle_errors(SCRIPT_NAME, logger)
def main():
    logger.info(f"Starting {SCRIPT_NAME} execution")
    
    if DRY_RUN:
        logger.info("⚠️ RUNNING IN DRY_RUN MODE - No emails will be sent and no records updated")
        
    if not AIRTABLE_API_KEY:
        raise ValueError("AIRTABLE_API_KEY environment variable is not set")
        
    # 1. Get Gmail service
    try:
        gmail_service = get_gmail_service()
        logger.info("Successfully authenticated with Gmail API")
    except Exception as e:
        logger.error(f"Failed to authenticate with Gmail API: {str(e)}")
        return
        
    # 2. Fetch prospects
    prospects = get_qualified_prospects()
    
    if not prospects:
        logger.info("No qualified prospects found. Exiting.")
        return
        
    # 3. Process prospects
    emails_sent = 0
    
    for prospect in prospects:
        if emails_sent >= MAX_EMAILS_PER_RUN:
            logger.info(f"Reached MAX_EMAILS_PER_RUN ({MAX_EMAILS_PER_RUN}). Stopping for this run.")
            break
            
        record_id = prospect.get("id")
        fields = prospect.get("fields", {})
        
        email = fields.get("Email", "").strip()
        first_name = fields.get("First Name", "there").strip()
        company = fields.get("Company", "your company").strip()
        
        logger.info(f"Processing prospect: {first_name} at {company} ({email})")
        
        # Validation
        if not is_valid_email(email):
            logger.warning(f"Invalid email format for {record_id}: {email}. Skipping.")
            continue
            
        # Check state to prevent duplicates
        state_key = f"{SCRIPT_NAME}_{record_id}"
        state = state_manager.get_state(state_key)
        
        if state.get("status") == "success":
            logger.info(f"Record {record_id} already processed successfully. Skipping.")
            continue
            
        # Generate email content
        subject = get_email_subject(company)
        body = get_email_body(first_name, company)
        
        # Send email
        email_success = send_email(gmail_service, email, subject, body)
        
        if email_success:
            # Update Airtable
            update_success = update_airtable_record(record_id)
            
            if update_success:
                # Update state
                state_manager.update_state(
                    state_key,
                    last_processed_id=record_id,
                    last_processed_timestamp=datetime.now().isoformat(),
                    status="success"
                )
                emails_sent += 1
                logger.info(f"Successfully completed workflow for {record_id}")
            else:
                logger.error(f"Email sent but Airtable update failed for {record_id}")
                state_manager.update_state(
                    state_key,
                    last_processed_id=record_id,
                    last_processed_timestamp=datetime.now().isoformat(),
                    status="error_airtable_update"
                )
        else:
            logger.error(f"Failed to send email for {record_id}")
            state_manager.update_state(
                state_key,
                last_processed_id=record_id,
                last_processed_timestamp=datetime.now().isoformat(),
                status="error_email_send"
            )
            
    logger.info(f"Execution complete. Sent {emails_sent} emails.")

if __name__ == "__main__":
    main()
