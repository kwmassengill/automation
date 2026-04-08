#!/usr/bin/env python3
"""
Script 4: Not Qualified - Polite Decline
=========================================

Purpose:
    Sends a polite decline email to prospects marked as "Not Qualified" in Airtable,
    then updates their record to mark the email as sent.

Trigger:
    Runs every 15 minutes via LaunchAgent (configurable)

Workflow:
    1. Fetch records from Airtable where:
       - Qualification Status = "Not Qualified"
       - Email is not blank
       - In Automation = TRUE
    2. For each record (limited by MAX_EMAILS_PER_RUN):
       - Check if already processed (state tracking)
       - Send polite decline email via Gmail OAuth
       - Update Airtable record with Date Sent and new status
       - Track in state database
    3. Log all operations and errors
    4. Send error notification if something fails

Author: Manus AI
Date: March 23, 2026
Version: 1.0
"""

import os
import sys
import re
import base64
import logging
import traceback
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail OAuth imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Add parent directory to path for shared_utils import
sys.path.insert(0, str(Path(__file__).parent))

from shared_utils import setup_logger, send_error_notification, StateManager, handle_errors

# Load environment variables
load_dotenv('/Users/kevinmassengill/Automations/config/.env')

# ============================================================================
# SAFEGUARD SETTINGS - CRITICAL FOR PRODUCTION
# ============================================================================
DRY_RUN = False  # Set to True for testing without sending emails
MAX_EMAILS_PER_RUN = 1  # Only 1 email per execution - MANDATORY for safety

# ============================================================================
# CONFIGURATION
# ============================================================================
SCRIPT_NAME = "script_04_not_qualified_polite_decline"
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = "appoNkgoKHAUXgXV9"
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"

# Gmail OAuth configuration
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
GMAIL_CREDS_FILE = Path.home() / "Automations" / "config" / "oauth_credentials.json"
GMAIL_TOKEN_FILE = Path.home() / "Automations" / "config" / "oauth_token.json"

# Paths
CONFIG_DIR = Path.home() / "Automations" / "config"
STATE_DB_PATH = CONFIG_DIR / "state.db"
LOGS_DIR = Path.home() / "Automations" / "logs"

# Airtable field IDs (from blueprint analysis)
FIELD_IDS = {
    "date_sent": "fldI2tIVJyDy1Cymi",
    "qualification_status": "fldgCH6CyIsNUCkV8",
    "email": "fldBg1qqf4RM1RCyu",
    "first_name": "fld6jEciITAhhMj7w",
    "company": "fld9QhGE9uzOOEjSg",
}

# Email template configuration
EMAIL_SUBJECT = "Re - {{Company}}"
EMAIL_BODY_HTML = """
<div style="font-family: 'Times New Roman', Times, serif; font-size: 14px; color: #000000;">
    <p style="margin: 0 0 15px 0;">Hi {{First Name}},</p>
    
    <p style="margin: 0 0 15px 0;">Thanks for taking the time to share those details about {{Company}}. Based on what you've described, our Annuity Sale model may not be the best fit for your current situation. Our structure works best for companies with greater than $1 million in free cash flow and owners ready to transition within 3-6 months.</p>
    
    <p style="margin: 0 0 15px 0;">I appreciate you considering us, and I wish you all the best with your exit planning.</p>
    
    <p style="margin: 0 0 15px 0;">Cordially,</p>
    
    <p style="margin: 0;">Best regards,  
  

Kevin Massengill  

Meraglim Holdings Corporation  

KMassengill@Meraglim.com</p>
</div>
"""

# Initialize logger
logger = setup_logger(SCRIPT_NAME)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_valid_email(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def get_gmail_service():
    """
    Get authenticated Gmail API service using OAuth 2.0.
    
    Handles token refresh and new authentication flow if needed.
    
    Returns:
        Gmail API service object
        
    Raises:
        FileNotFoundError: If credentials file not found
        Exception: If authentication fails
    """
    creds = None
    
    # Load existing token if available
    if GMAIL_TOKEN_FILE.exists():
        logger.debug(f"Loading existing Gmail token from {GMAIL_TOKEN_FILE}")
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), GMAIL_SCOPES)
    
    # Check if token is valid or needs refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Gmail token")
            creds.refresh(Request())
        else:
            # Need new authentication
            if not GMAIL_CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {GMAIL_CREDS_FILE}. "
                    "Please set up OAuth credentials first."
                )
            
            logger.info("Starting new Gmail OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GMAIL_CREDS_FILE),
                GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save token for future use
        logger.debug(f"Saving Gmail token to {GMAIL_TOKEN_FILE}")
        with open(GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def send_email(service, to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email using Gmail API.
    
    Args:
        service: Gmail API service object
        to_email: Recipient email address
        subject: Email subject
        html_body: Email body in HTML format
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Validate email
        if not is_valid_email(to_email):
            logger.warning(f"Invalid email format: {to_email}")
            return False
        
        # Create message
        message = MIMEMultipart('alternative')
        message['to'] = to_email
        message['subject'] = subject
        
        # Attach HTML body
        msg_body = MIMEText(html_body, 'html')
        message.attach(msg_body)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Check DRY_RUN mode
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would send email to {to_email} with subject: {subject}")
            return True
        
        # Send email
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        logger.info(f"Successfully sent email to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
        return False


def get_prospects_to_decline() -> List[Dict]:
    """
    Fetch prospects from Airtable that are marked as "Not Qualified".
    
    Filter criteria:
    - Qualification Status = "Not Qualified"
    - Email is not blank
    - In Automation = TRUE
    
    Returns:
        List of prospect records
    """
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        }
        
        # Build filter formula
        filter_formula = (
            "AND("
            "{Qualification Status} = 'Not Qualified', "
            "NOT({Email} = BLANK()), "
            "{In Automation} = TRUE()"
            ")"
        )
        
        params = {
            "filterByFormula": filter_formula,
            "maxRecords": MAX_EMAILS_PER_RUN * 2,  # Fetch extra in case some are already processed
            "sort[0][field]": "Last Modified",
            "sort[0][direction]": "desc"
        }
        
        logger.info(f"Fetching prospects with formula: {filter_formula}")
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        records = response.json().get("records", [])
        logger.info(f"Found {len(records)} prospects matching criteria")
        
        return records
        
    except Exception as e:
        logger.error(f"Failed to fetch prospects from Airtable: {str(e)}", exc_info=True)
        raise


def update_airtable_record(record_id: str, date_sent: str) -> bool:
    """
    Update Airtable record after sending email.
    
    Updates:
    - Date Sent: Current timestamp
    - Qualification Status: "Declined Email Sent"
    
    Args:
        record_id: Airtable record ID
        date_sent: ISO format timestamp
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}/{record_id}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "fields": {
                FIELD_IDS["date_sent"]: date_sent,
                FIELD_IDS["qualification_status"]: "Declined Email Sent"
            }
        }
        
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would update record {record_id} with: {payload}")
            return True
        
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        
        logger.info(f"Successfully updated Airtable record {record_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update Airtable record {record_id}: {str(e)}", exc_info=True)
        return False


def personalize_email(template: str, prospect: Dict) -> str:
    """
    Personalize email template with prospect data.
    
    Args:
        template: Email template with {{placeholders}}
        prospect: Prospect record from Airtable
        
    Returns:
        Personalized email body
    """
    result = template
    
    # Extract fields from prospect record
    fields = prospect.get("fields", {})
    first_name = fields.get("First Name", "there")
    company = fields.get("Company", "your company")
    
    # Replace placeholders
    result = result.replace("{{First Name}}", first_name)
    result = result.replace("{{Company}}", company)
    
    return result


@handle_errors(SCRIPT_NAME, logger)
def main():
    """
    Main execution function.
    
    Orchestrates the entire workflow:
    1. Fetch prospects marked as "Not Qualified"
    2. For each prospect (up to MAX_EMAILS_PER_RUN):
       - Check if already processed
       - Send polite decline email
       - Update Airtable record
       - Track in state database
    """
    logger.info(f"Starting {SCRIPT_NAME} execution")
    logger.info(f"DRY_RUN: {DRY_RUN}, MAX_EMAILS_PER_RUN: {MAX_EMAILS_PER_RUN}")
    
    # Initialize state manager
    state_manager = StateManager(str(STATE_DB_PATH))
    
    # Verify configuration
    if not AIRTABLE_API_KEY:
        raise ValueError("AIRTABLE_API_KEY not set in environment variables")
    
    # Get Gmail service
    try:
        gmail_service = get_gmail_service()
        logger.info("Gmail service authenticated successfully")
    except Exception as e:
        logger.error(f"Failed to authenticate Gmail: {str(e)}", exc_info=True)
        raise
    
    # Fetch prospects
    try:
        prospects = get_prospects_to_decline()
    except Exception as e:
        logger.error(f"Failed to fetch prospects: {str(e)}", exc_info=True)
        raise
    
    if not prospects:
        logger.info("No prospects found matching criteria. Exiting.")
        return True
    
    # Process prospects
    emails_sent = 0
    errors = 0
    
    for prospect in prospects:
        # Check if we've reached the limit
        if emails_sent >= MAX_EMAILS_PER_RUN:
            logger.info(f"Reached MAX_EMAILS_PER_RUN limit ({MAX_EMAILS_PER_RUN}). Stopping.")
            break
        
        record_id = prospect.get("id")
        fields = prospect.get("fields", {})
        email = fields.get("Email")
        first_name = fields.get("First Name", "there")
        company = fields.get("Company", "your company")
        
        logger.info(f"Processing prospect: {first_name} ({email})")
        
        # Check if already processed
        state_key = f"{SCRIPT_NAME}_{record_id}"
        state = state_manager.get_state(state_key)
        
        if state.get("status") == "success":
            logger.info(f"Record {record_id} already processed. Skipping.")
            continue
        
        # Validate email
        if not is_valid_email(email):
            logger.warning(f"Invalid email for {first_name}: {email}. Skipping.")
            state_manager.update_state(
                state_key,
                last_processed_id=record_id,
                last_processed_timestamp=datetime.now().isoformat(),
                status="skipped"
            )
            continue
        
        # Prepare email
        subject = EMAIL_SUBJECT.replace("{{Company}}", company)
        body = personalize_email(EMAIL_BODY_HTML, prospect)
        
        # Send email
        email_sent = send_email(gmail_service, email, subject, body)
        
        if not email_sent:
            logger.error(f"Failed to send email to {email}")
            errors += 1
            state_manager.update_state(
                state_key,
                last_processed_id=record_id,
                last_processed_timestamp=datetime.now().isoformat(),
                status="error"
            )
            continue
        
        # Update Airtable record
        date_sent = datetime.utcnow().isoformat() + "Z"
        record_updated = update_airtable_record(record_id, date_sent)
        
        if not record_updated:
            logger.error(f"Failed to update Airtable record for {email}")
            errors += 1
            state_manager.update_state(
                state_key,
                last_processed_id=record_id,
                last_processed_timestamp=datetime.now().isoformat(),
                status="error"
            )
            continue
        
        # Mark as processed
        state_manager.update_state(
            state_key,
            last_processed_id=record_id,
            last_processed_timestamp=datetime.now().isoformat(),
            status="success"
        )
        
        emails_sent += 1
        logger.info(f"Successfully processed prospect {first_name} ({email})")
    
    # Log summary
    logger.info(f"Execution complete: {emails_sent} emails sent, {errors} errors")
    
    if errors > 0:
        logger.warning(f"Script completed with {errors} error(s)")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error in {SCRIPT_NAME}: {str(e)}", exc_info=True)
        send_error_notification(
            SCRIPT_NAME,
            f"Fatal error: {str(e)}",
            traceback.format_exc(),
            logger
        )
        sys.exit(1)
