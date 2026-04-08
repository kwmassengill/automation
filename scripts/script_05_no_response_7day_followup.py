#!/usr/bin/env python3
"""
Script 5: No Response - 7 Day Follow Up

Watches for prospects with no response after 7 days and sends a follow-up email.
Then updates the Airtable record to mark the follow-up as sent.

Trigger: Records in Airtable where 7 days have passed since initial contact
Actions:
  1. Check for prospects with no response after 7 days
  2. Send follow-up email via Gmail
  3. Update Airtable record with follow-up sent status

Schedule: Every 5 minutes via cron
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for shared utilities
sys.path.insert(0, str(Path(__file__).parent))

from shared_utils import setup_logger, StateManager, send_error_notification, handle_errors

# Third-party imports
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

# Load environment variables
load_dotenv()

# Configuration
SCRIPT_NAME = "script_05_no_response_7day_followup"
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appoNkgoKHAUXgXV9")
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"  # Prospects table

GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "/Users/kevinmassengill/Automations/config/google_token.json")

# Initialize logger and state manager
logger = setup_logger(SCRIPT_NAME)
state_manager = StateManager()


class AirtableClient:
    """Client for Airtable API operations."""
    
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
    
    def get_records(self, table_id: str, filter_formula: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get records from Airtable with optional filter."""
        url = f"{self.base_url}/{self.base_id}/{table_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if filter_formula:
            params["filterByFormula"] = filter_formula
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("records", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Airtable records: {str(e)}")
            raise
    
    def update_record(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> bool:
        """Update a record in Airtable."""
        url = f"{self.base_url}/{self.base_id}/{table_id}/{record_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {"fields": fields}
        
        try:
            response = requests.patch(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"Updated Airtable record {record_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating Airtable record: {str(e)}")
            raise


class GmailClient:
    """Client for Gmail API operations."""
    
    def __init__(self, token_file: str):
        self.token_file = token_file
        self.service = self._get_service()
    
    def _get_service(self):
        """Get Gmail service."""
        try:
            creds = Credentials.from_authorized_user_file(self.token_file)
            return build("gmail", "v1", credentials=creds)
        except Exception as e:
            logger.error(f"Error initializing Gmail service: {str(e)}")
            raise
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email via Gmail."""
        try:
            message = MIMEText(body, "html")
            message["to"] = to_email
            message["subject"] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {"raw": raw_message}
            
            self.service.users().messages().send(userId="me", body=send_message).execute()
            logger.info(f"Follow-up email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise


def get_prospects_for_followup() -> List[Dict[str, Any]]:
    """Get prospects that need 7-day follow-up emails."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    # Calculate the date 7 days ago
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    
    # Filter for records where:
    # - Status is not "Qualified" or "Not Qualified"
    # - Email was sent more than 7 days ago
    # - 7-day follow-up hasn't been sent yet
    filter_formula = f"""AND(
        {{Email Sent Date}} <= '{seven_days_ago}',
        {{Status}} = 'Pending',
        {{7-Day Follow-up Sent}} = FALSE()
    )"""
    
    try:
        records = airtable.get_records(AIRTABLE_TABLE_ID, filter_formula)
        logger.info(f"Found {len(records)} prospects for 7-day follow-up")
        return records
    
    except Exception as e:
        logger.error(f"Error getting prospects for follow-up: {str(e)}")
        raise


def send_followup_email(prospect: Dict[str, Any]) -> bool:
    """Send a 7-day follow-up email to a prospect."""
    gmail = GmailClient(GOOGLE_TOKEN_FILE)
    
    fields = prospect.get("fields", {})
    email = fields.get("Email")
    first_name = fields.get("First Name", "Prospect")
    
    if not email:
        logger.warning(f"Prospect {prospect['id']} has no email address")
        return False
    
    subject = "Following Up - Meraglim Holdings Opportunity"
    body = f"""
    <html>
    <body>
    <p>Hi {first_name},</p>
    
    <p>I wanted to follow up on our previous conversation about potential opportunities with Meraglim Holdings.</p>
    
    <p>I haven't heard back from you, and I wanted to check in to see if you're still interested in exploring this opportunity. 
    If now isn't the right time, I completely understand—feel free to reach out whenever you're ready to discuss further.</p>
    
    <p>If you have any questions or would like to schedule a time to chat, please don't hesitate to reply to this email.</p>
    
    <p>Looking forward to hearing from you!</p>
    
    <p>Best regards,<br>
    Kevin Massengill<br>
    Meraglim Holdings Corporation<br>
    KMassengill@Meraglim.com</p>
    </body>
    </html>
    """
    
    try:
        gmail.send_email(email, subject, body)
        return True
    except Exception as e:
        logger.error(f"Error sending follow-up email to {email}: {str(e)}")
        return False


def update_prospect_status(prospect_id: str, followup_sent: bool = True) -> bool:
    """Update prospect record to mark 7-day follow-up as sent."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    fields = {
        "7-Day Follow-up Sent": followup_sent,
        "7-Day Follow-up Date": datetime.now().isoformat()
    }
    
    try:
        airtable.update_record(AIRTABLE_TABLE_ID, prospect_id, fields)
        return True
    except Exception as e:
        logger.error(f"Error updating prospect status: {str(e)}")
        return False


@handle_errors(SCRIPT_NAME, logger)
def main():
    """Main execution function."""
    logger.info(f"Starting {SCRIPT_NAME}")
    
    try:
        # Get prospects for follow-up
        prospects = get_prospects_for_followup()
        
        if not prospects:
            logger.info("No prospects for 7-day follow-up")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        # Process each prospect
        processed_count = 0
        for prospect in prospects:
            prospect_id = prospect["id"]
            fields = prospect.get("fields", {})
            
            logger.info(f"Processing follow-up for prospect: {fields.get('Name', 'Unknown')}")
            
            # Send follow-up email
            if send_followup_email(prospect):
                # Update Airtable record
                if update_prospect_status(prospect_id):
                    processed_count += 1
                    # Update state
                    state_manager.update_state(
                        SCRIPT_NAME,
                        last_processed_id=prospect_id,
                        last_processed_timestamp=datetime.now().isoformat(),
                        status="success"
                    )
        
        logger.info(f"Successfully sent {processed_count}/{len(prospects)} follow-up emails")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error sending follow-up emails: {str(e)}",
            str(e),
            logger
        )
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
