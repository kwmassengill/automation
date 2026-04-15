#!/usr/bin/env python3
"""
Script 3: Qualified Prospect - Calendar Invite

Watches for qualified prospects in Airtable and sends a calendar invite email.
Then updates the Airtable record to mark the invite as sent.

Trigger: Records in Airtable with "Status" = "Qualified"
Actions:
  1. Check for qualified prospects
  2. Send calendar invite email via Gmail
  3. Update Airtable record with invite sent status

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
SCRIPT_NAME = "script_03_qualified_prospect_calendar_invite"
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
            logger.info(f"Calendar invite sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise


def get_qualified_prospects() -> List[Dict[str, Any]]:
    """Get qualified prospects from Airtable that haven't received calendar invites."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    # Filter for records where Status = "Qualified" and Calendar Invite Not Sent
    filter_formula = "{Qualification Status} = 'Qualified'"
    
    try:
        records = airtable.get_records(AIRTABLE_TABLE_ID, filter_formula)
        logger.info(f"Found {len(records)} qualified prospects without calendar invites")
        return records
    
    except Exception as e:
        logger.error(f"Error getting qualified prospects: {str(e)}")
        raise


def send_calendar_invite(prospect: Dict[str, Any]) -> bool:
    """Send a calendar invite to a qualified prospect."""
    gmail = GmailClient(GOOGLE_TOKEN_FILE)
    
    fields = prospect.get("fields", {})
    email = fields.get("Email")
    first_name = fields.get("First Name", "Prospect")
    
    if not email:
        logger.warning(f"Prospect {prospect['id']} has no email address")
        return False
    
    # Create calendar invite for next available time slot
    meeting_time = datetime.now() + timedelta(days=3)
    meeting_time = meeting_time.replace(hour=10, minute=0, second=0)
    
    subject = "Let's Schedule a Meeting - Meraglim Holdings"
    body = f"""
    <html>
    <body>
    <p>Hi {first_name},</p>
    
    <p>Great news! We'd like to move forward with a meeting to discuss potential opportunities.</p>
    
    <p><strong>Proposed Meeting Time:</strong><br>
    {meeting_time.strftime('%A, %B %d, %Y at %I:%M %p')} (Central Time)</p>
    
    <p>Please let me know if this time works for you, or feel free to suggest an alternative time that's more convenient.</p>
    
    <p>Looking forward to our conversation!</p>
    
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
        logger.error(f"Error sending calendar invite to {email}: {str(e)}")
        return False


def update_prospect_status(prospect_id: str, invite_sent: bool = True) -> bool:
    """Update prospect record to mark calendar invite as sent."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    fields = {
        "Qualification Status": "Calendar Invite Sent",
        "Calendar Invite Date": datetime.now().isoformat()
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
        # Get qualified prospects
        prospects = get_qualified_prospects()
        
        if not prospects:
            logger.info("No qualified prospects to process")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        # Process each prospect
        processed_count = 0
        for prospect in prospects:
            prospect_id = prospect["id"]
            fields = prospect.get("fields", {})
            
            logger.info(f"Processing prospect: {fields.get('Name', 'Unknown')}")
            
            # Send calendar invite
            if send_calendar_invite(prospect):
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
        
        logger.info(f"Successfully sent {processed_count}/{len(prospects)} calendar invites")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error sending calendar invites: {str(e)}",
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
