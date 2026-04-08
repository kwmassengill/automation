#!/usr/bin/env python3
"""
Script MHC-11: Post-Meeting Intelligence Sync

Watches for new emails with meeting notes/attachments and syncs meeting intelligence
data between Airtable and ClickUp. Extracts attachments and processes meeting records.

Trigger: New emails with meeting notes/attachments
Actions:
  1. Check for new emails with attachments
  2. Extract meeting notes and attachments
  3. Parse meeting intelligence data
  4. Update Airtable records
  5. Create/update ClickUp tasks with meeting summary
  6. Post analysis comments

Schedule: Every 5 minutes via cron

NOTE: This is a complex workflow. The actual implementation will depend on:
- The email format and attachment types
- The structure of meeting notes
- The specific routing rules you want to apply
"""

import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for shared utilities
sys.path.insert(0, str(Path(__file__).parent))

from shared_utils import setup_logger, StateManager, send_error_notification, handle_errors

# Third-party imports
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load credentials using centralized loader
from shared_utils import load_credentials
creds = load_credentials()

# Configuration
SCRIPT_NAME = "script_mhc11_post_meeting_intelligence_sync"
GOOGLE_TOKEN_FILE = creds["GOOGLE_TOKEN_FILE"]

AIRTABLE_API_KEY = creds["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = creds["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")

# Initialize logger and state manager
logger = setup_logger(SCRIPT_NAME)
state_manager = StateManager()


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
    
    def get_emails_with_attachments(self, query: str = "has:attachment", 
                                   max_results: int = 10) -> List[Dict[str, Any]]:
        """Get emails with attachments."""
        try:
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get("messages", [])
            logger.info(f"Found {len(messages)} emails with attachments")
            
            email_data = []
            for msg in messages:
                msg_data = self.get_message_with_attachments(msg["id"])
                if msg_data:
                    email_data.append(msg_data)
            
            return email_data
        except Exception as e:
            logger.error(f"Error getting emails: {str(e)}")
            raise
    
    def get_message_with_attachments(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message with attachment information."""
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()
            
            headers = message["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "")
            
            # Extract attachments
            attachments = []
            if "parts" in message["payload"]:
                for part in message["payload"]["parts"]:
                    if part.get("filename"):
                        attachments.append({
                            "filename": part["filename"],
                            "mimeType": part["mimeType"],
                            "partId": part["partId"],
                            "size": part["size"]
                        })
            
            # Get email body
            body = ""
            if "parts" in message["payload"]:
                for part in message["payload"]["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part["body"].get("data", "")
                        if data:
                            body = base64.urlsafe_b64decode(data).decode("utf-8")
                            break
            else:
                data = message["payload"]["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
            
            return {
                "id": message_id,
                "subject": subject,
                "sender": sender,
                "body": body,
                "attachments": attachments,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting message details: {str(e)}")
            return None


class MeetingIntelligenceProcessor:
    """Process post-meeting intelligence data."""
    
    @staticmethod
    def extract_meeting_notes(email_body: str) -> Dict[str, Any]:
        """
        Extract meeting notes from email body.
        
        Looks for common meeting note patterns and structures.
        """
        notes = {
            "attendees": [],
            "discussion_points": [],
            "action_items": [],
            "next_steps": "",
            "sentiment": "neutral"
        }
        
        # Simple parsing - in production, you might use NLP
        lines = email_body.split("\n")
        
        current_section = None
        for line in lines:
            line = line.strip()
            
            if "attendee" in line.lower():
                current_section = "attendees"
            elif "discussion" in line.lower() or "talked about" in line.lower():
                current_section = "discussion"
            elif "action" in line.lower() or "todo" in line.lower():
                current_section = "action"
            elif "next" in line.lower() or "follow" in line.lower():
                current_section = "next"
            elif line and current_section:
                if current_section == "attendees":
                    notes["attendees"].append(line)
                elif current_section == "discussion":
                    notes["discussion_points"].append(line)
                elif current_section == "action":
                    notes["action_items"].append(line)
                elif current_section == "next":
                    notes["next_steps"] = line
        
        return notes


@handle_errors(SCRIPT_NAME, logger)
def main():
    """Main execution function."""
    logger.info(f"Starting {SCRIPT_NAME}")
    
    try:
        gmail = GmailClient(GOOGLE_TOKEN_FILE)
        
        # Get emails with attachments
        emails = gmail.get_emails_with_attachments(max_results=10)
        
        if not emails:
            logger.info("No emails with attachments to process")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        # Process each email
        processed_count = 0
        for email in emails:
            logger.info(f"Processing email from {email['sender']}: {email['subject']}")
            
            # Extract meeting notes from email body
            meeting_notes = MeetingIntelligenceProcessor.extract_meeting_notes(email["body"])
            
            logger.info(f"Extracted meeting notes: {len(meeting_notes['discussion_points'])} discussion points")
            
            # TODO: Implement the following:
            # 1. Find corresponding prospect/meeting in Airtable
            # 2. Update Airtable with meeting notes
            # 3. Create/update ClickUp task with meeting summary
            # 4. Post analysis comments
            # 5. Download and process attachments if needed
            
            processed_count += 1
            
            # Update state
            state_manager.update_state(
                SCRIPT_NAME,
                last_processed_id=email["id"],
                last_processed_timestamp=datetime.now().isoformat(),
                status="success"
            )
        
        logger.info(f"Successfully processed {processed_count}/{len(emails)} emails")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error in post-meeting intelligence sync: {str(e)}",
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
