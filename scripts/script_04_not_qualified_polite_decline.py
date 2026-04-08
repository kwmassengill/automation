#!/usr/bin/env python3
"""
Script 4: Not Qualified - Polite Decline

Watches for prospects marked as "Not Qualified" in Airtable and sends a polite decline email.
Then updates the Airtable record to mark the email as sent.

Trigger: Records in Airtable with "Qualification Status" = "Not Qualified"
Actions:
  1. Check for not qualified prospects
  2. Send polite decline email via Gmail
  3. Update Airtable record with decline email sent status
  4. Update Deal Phase to "Disqualified — No fit or no budget"
  5. Update Deal Phase Date to current date

Schedule: Every 15 minutes via LaunchAgent
"""

import os
import sys
from datetime import datetime
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
load_dotenv("/Users/kevinmassengill/Automations/config/.env")

# Configuration
SCRIPT_NAME = "script_04_not_qualified_polite_decline"
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
    
    def get_records(self, table_id: str, filter_formula: Optional[str] = None ) -> List[Dict[str, Any]]:
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
            logger.info(f"Decline email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise


def get_not_qualified_prospects() -> List[Dict[str, Any]]:
    """Get not qualified prospects from Airtable that haven't received decline emails."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    # Filter for records where Qualification Status = "Not Qualified" and Email is not blank
    filter_formula = "AND({Qualification Status} = 'Not Qualified', {Email} != '')"
    
    try:
        records = airtable.get_records(AIRTABLE_TABLE_ID, filter_formula)
        logger.info(f"Found {len(records)} not qualified prospects")
        return records
    
    except Exception as e:
        logger.error(f"Error getting not qualified prospects: {str(e)}")
        raise


def send_decline_email(prospect: Dict[str, Any]) -> bool:
    """Send a polite decline email to a prospect."""
    gmail = GmailClient(GOOGLE_TOKEN_FILE)
    
    fields = prospect.get("fields", {})
    email = fields.get("Email")
    first_name = fields.get("First Name", "Prospect")
    company = fields.get("Company", "")
    
    if not email:
        logger.warning(f"Prospect {prospect['id']} has no email address")
        return False
    
    subject = "Thank You for Your Interest in Meraglim Holdings"
    body = f"""
    <html>
    <body>
    <p>Hi {first_name},</p>
    
    <p>Thank you for your interest in Meraglim Holdings and the opportunity to learn about {company}.</p>
    
    <p>After careful consideration, we've determined that at this time, our current focus and resources are directed 
    toward different market segments and business models. However, we appreciate the time you took to speak with us.</p>
    
    <p>We'd like to keep your information on file, and should our strategic priorities shift in the future, we'll certainly 
    reach out to explore potential opportunities.</p>
    
    <p>Best of luck with your endeavors, and we hope to connect again in the future.</p>
    
    <p>Best regards,  

    Kevin Massengill  

    Meraglim Holdings Corporation  

    KMassengill@Meraglim.com</p>
    </body>
    </html>
    """
    
    try:
        gmail.send_email(email, subject, body)
        return True
    except Exception as e:
        logger.error(f"Error sending decline email to {email}: {str(e)}")
        return False


def update_prospect_status(prospect_id: str, email_sent: bool = True) -> bool:
    """Update prospect record to mark decline email as sent and update deal phase."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    # Get current date in YYYY-MM-DD format
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    fields = {
        "Qualification Status": "Declined Email Sent",
        "Deal Phase": "Disqualified — No fit or no budget",
        "Deal Phase Date": current_date
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
        # Get not qualified prospects
        prospects = get_not_qualified_prospects()
        
        if not prospects:
            logger.info("No not qualified prospects to process")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        # Process each prospect
        processed_count = 0
        for prospect in prospects:
            prospect_id = prospect["id"]
            fields = prospect.get("fields", {})
            
            logger.info(f"Processing prospect: {fields.get('Name', 'Unknown')}")
            
            # Send decline email
            if send_decline_email(prospect):
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
        
        logger.info(f"Successfully sent {processed_count}/{len(prospects)} decline emails")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error sending decline emails: {str(e)}",
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
