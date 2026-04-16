#!/usr/bin/env python3
"""
Script 5: No Response - 7 Day Follow Up
Purpose: Sends a follow-up email to prospects who received the initial qualification email 7 days ago but haven't responded.
Trigger: Every 15 minutes via LaunchAgent
"""

import os
import sys
import json
import base64
import requests
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText

# Gmail OAuth imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

# Add the project directory to the path so we can import shared_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from shared_utils import setup_logger, handle_errors, StateManager, check_network_connectivity

# ============================================================================
# SAFEGUARD SETTINGS
# ============================================================================
DRY_RUN = False  # Set to False for production
MAX_EMAILS_PER_RUN = 5  # Prevent mass operations

# ============================================================================
# CONFIGURATION
# ============================================================================
SCRIPT_NAME = "script_05_no_response_7_day_followup"

# Load credentials using centralized loader
from shared_utils import load_credentials
creds = load_credentials()

AIRTABLE_API_KEY = creds["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = creds["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"

# Paths
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", os.path.expanduser("~/Automations/config")))
STATE_DB_PATH = CONFIG_DIR / "state.db"
# Use the same google_token.json as all other scripts
GOOGLE_TOKEN_PATH = CONFIG_DIR / "google_token.json"

# Gmail OAuth scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Field IDs (from Airtable metadata)
FIELD_IDS = {
    "first_name": "fld6jEciITAhhMj7w",
    "company": "fld9QhGE9uzOOEjSg",
    "email": "fldBg1qqf4RM1RCyu",
    "qualification_status": "fldgCH6CyIsNUCkV8",
    "date_sent": "fldI2tIVJyDy1Cymi",
    "in_automation": "fldArNm1cnJ1zaO8O",
    "days_since_email": "flde4VDrWEJBNevfM",
    "deal_phase": "fld07a0yFNwo92lTs",
    "deal_phase_date": "fldNZDQaLsGJoQQhn"
}

# Initialize logger
logger = setup_logger(SCRIPT_NAME)

# ============================================================================
# AIRTABLE FUNCTIONS
# ============================================================================

def get_followup_prospects() -> List[Dict]:
    """Fetch prospects from Airtable that need a 7-day follow-up."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    }
    
    # Filter logic based on Blueprint 5:
    # 1. Qualification Status = "Qualification Email Sent"
    # 2. Email exists
    # 3. In Automation = true
    # 4. Date Sent exists
    # 5. Days Since Email >= 7
    
    filter_formula = "AND(" \
                     "{Qualification Status} = 'Qualification Email Sent', " \
                     "NOT({Email} = BLANK()), " \
                     "{In Automation} = TRUE(), " \
                     "NOT({Date Sent} = BLANK()), " \
                     "{Days Since Email} >= 7" \
                     ")"
    
    params = {
        "filterByFormula": filter_formula,
        "maxRecords": MAX_EMAILS_PER_RUN,
        "sort[0][field]": "Last Modified",
        "sort[0][direction]": "desc"
    }
    
    logger.info(f"Fetching prospects with formula: {filter_formula}")
    
    response = requests.get(url, headers=headers, params=params)
    
    if not response.ok:
        logger.error(f"Airtable API Error: {response.status_code} - {response.text}")
        response.raise_for_status()
        
    records = response.json().get("records", [])
    logger.info(f"Found {len(records)} prospects matching criteria")
    return records

def update_airtable_record(record_id: str) -> bool:
    """Update Airtable record after sending follow-up."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    current_time = datetime.utcnow().isoformat() + "Z"
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    payload = {
        "fields": {
            FIELD_IDS["qualification_status"]: "No Response - Followed Up",
            FIELD_IDS["date_sent"]: current_time,
            FIELD_IDS["deal_phase"]: "Passed — Did not proceed (preserve for reference)",
            FIELD_IDS["deal_phase_date"]: current_date
        }
    }
    
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would update record {record_id} with: {payload}")
        return True
    
    response = requests.patch(url, headers=headers, json=payload)
    
    if not response.ok:
        logger.error(f"Airtable Update Error: {response.status_code} - {response.text}")
        response.raise_for_status()
        
    logger.info(f"Successfully updated Airtable record {record_id}")
    return True

# ============================================================================
# EMAIL FUNCTIONS
# ============================================================================

def get_email_body(first_name: str, company_name: str) -> str:
    """Generate the HTML email body."""
    return f"""
    <div style="font-family: 'Times New Roman', Times, serif; font-size: 14px; color: #000000;">
        <p style="margin: 0 0 15px 0;">Hi {first_name},</p>
        
        <p style="margin: 0 0 15px 0;">I wanted to follow up on my previous email about potential exit options for {company_name}.</p>
        
        <p style="margin: 0 0 15px 0;">I know you're busy, so I'll keep this brief: if our Annuity Sale approach isn't a fit or the timing isn't right, no problem at all - just let me know and I'll close the loop.</p>
        
        <p style="margin: 0 0 15px 0;">But if you're still curious about how a structured 10-year payout could give you a higher sale price with better tax treatment, I'm happy to share more details.</p>
        
        <p style="margin: 0 0 15px 0;">Here is a 5-minute video that quickly explains our offer:</p>
        
        <div style="margin: 20px 0;">
            <a href="https://youtu.be/L0WIPiMFtRs" style="display: inline-block; padding: 12px 28px; background-color: #C9A84C; color: #1A1A1A; text-decoration: none; border-radius: 4px; font-weight: bold; font-family: Arial, sans-serif; font-size: 15px;">▶ Watch the 5-Minute Overview</a>
        </div>
        
        <p style="margin: 0 0 15px 0;">Either way, I'd appreciate a quick reply so I know where things stand.</p>
        
        <p style="margin: 0 0 15px 0;">Cordially,</p>
        
        <p style="margin: 0; padding: 0;">Kevin Massengill</p>
        <p style="margin: 0; padding: 0;">Chairman & CEO</p>
        <p style="margin: 0; padding: 0;">Meraglim Holdings Corporation</p>
        <p style="margin: 0; padding: 0;">kmassengill@meraglim.com</p>
    </div>
    """

def get_gmail_service():
    """Get Gmail service with OAuth 2.0 authentication using google_token.json."""
    token_creds = None
    
    # Load existing token (same google_token.json used by all other scripts)
    if os.path.exists(GOOGLE_TOKEN_PATH):
        token_creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_PATH), GMAIL_SCOPES)
    
    # Refresh if expired
    if token_creds and token_creds.expired and token_creds.refresh_token:
        try:
            token_creds.refresh(Request())
            # Save refreshed token
            with open(GOOGLE_TOKEN_PATH, 'w') as token_file:
                token_file.write(token_creds.to_json())
            logger.info("Gmail OAuth token refreshed successfully")
        except RefreshError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return None
    
    if not token_creds or not token_creds.valid:
        logger.error(f"Gmail OAuth token not valid. Please re-authorize by running script_02 or another OAuth script first.")
        return None
    
    return build('gmail', 'v1', credentials=token_creds)

def send_email(service, to_email: str, subject: str, body_html: str) -> bool:
    """Send email via Gmail OAuth."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would send email to {to_email}")
        logger.info(f"[DRY RUN] Subject: {subject}")
        logger.debug(f"[DRY RUN] Body: {body_html}")
        return True
        
    try:
        # Create the email message
        message = MIMEText(body_html, 'html')
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = 'kmassengill@meraglim.com'
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {'raw': raw_message}
        
        result = service.users().messages().send(userId='me', body=send_message).execute()
        logger.info(f"Email sent successfully to {to_email}, message ID: {result['id']}")
        return True
            
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

@handle_errors(SCRIPT_NAME, logger)
def main():
    logger.info(f"Starting {SCRIPT_NAME} execution (DRY_RUN={DRY_RUN})")
    check_network_connectivity(logger)

    if not AIRTABLE_API_KEY:
        logger.error("AIRTABLE_API_KEY environment variable is not set.")
        return False
    
    # Get Gmail service
    service = get_gmail_service()
    if not service:
        logger.error("Failed to initialize Gmail service")
        return False
        
    state_manager = StateManager(str(STATE_DB_PATH))
    
    # 1. Fetch prospects
    prospects = get_followup_prospects()
    
    if not prospects:
        logger.info("No prospects found requiring 7-day follow-up.")
        return True
        
    emails_sent = 0
    
    # 2. Process each prospect
    for record in prospects:
        if emails_sent >= MAX_EMAILS_PER_RUN:
            logger.info(f"Reached MAX_EMAILS_PER_RUN ({MAX_EMAILS_PER_RUN}). Stopping.")
            break
            
        record_id = record.get("id")
        fields = record.get("fields", {})
        
        # Extract fields
        first_name = fields.get("First Name", "")
        company = fields.get("Company", "")
        email = fields.get("Email", "")
        
        if not email:
            logger.warning(f"Record {record_id} has no email address. Skipping.")
            continue
            
        # Check state to prevent duplicates
        state_key = f"{SCRIPT_NAME}_{record_id}_followup"
        state = state_manager.get_state(state_key)
        
        if state.get("status") == "success":
            logger.info(f"Follow-up already sent for {record_id}. Skipping.")
            continue
            
        logger.info(f"Processing follow-up for {first_name} at {company} ({email})")
        
        # 3. Prepare and send email
        subject = f"Following Up - {company}"
        body_html = get_email_body(first_name, company)
        
        email_success = send_email(service, email, subject, body_html)
        
        if email_success:
            # 4. Update Airtable
            update_success = update_airtable_record(record_id)
            
            if update_success:
                # 5. Update state
                if not DRY_RUN:
                    state_manager.update_state(
                        state_key,
                        last_processed_id=record_id,
                        last_processed_timestamp=datetime.now().isoformat(),
                        status="success"
                    )
                logger.info(f"Successfully completed follow-up process for {record_id}")
                emails_sent += 1
            else:
                logger.error(f"Failed to update Airtable for {record_id} after sending email.")
        else:
            logger.error(f"Failed to send email to {email} for record {record_id}.")
            
    logger.info(f"Finished {SCRIPT_NAME} execution. Processed {emails_sent} records.")
    return True

if __name__ == "__main__":
    main()
