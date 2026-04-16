#!/usr/bin/env python3
"""
Script MHC-11: Post-Meeting Intelligence Sync (Complete Implementation)
Watches for new emails with meeting transcripts and syncs meeting intelligence
between Gmail, Airtable, and ClickUp.
"""

import os
import sys
import json
import base64
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

from shared_utils import setup_logger, StateManager, send_error_notification, handle_errors

import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import anthropic

load_dotenv()

SCRIPT_NAME = "script_mhc11_post_meeting_intelligence_sync"
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "/Users/kevinmassengill/Automations/config/google_token.json")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appoNkgoKHAUXgXV9")
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"
CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

CLICKUP_WORKSPACE_ID = "9017878084"
CLICKUP_SPACE_ID = "90174046780"
CLICKUP_NEXT_ACTIONS_LIST_ID = "901711661107"
CLICKUP_MEETING_SUMMARIES_LIST_ID = "901711661162"
CLICKUP_PROSPECT_EMAIL_FIELD_ID = "0840ee8f-0404-491a-957e-eef855b72295"

CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 1000

logger = setup_logger(SCRIPT_NAME)
state_manager = StateManager()

EXTERNAL_SYSTEM_PROMPT = """You are a post-meeting intelligence analyst for Meraglim Holdings Corporation.
Meraglim is an investment holding company focused on acquisitions in the
cybersecurity and defense sector. Kevin Massengill is Chairman and CEO.
The acquisition profile is: motivated seller, solid cash flow, $3-15M revenue
range, cybersecurity or defense sector.

You will receive a meeting transcript. Analyze it thoroughly and return ONLY
a valid JSON object with no preamble, no markdown, and no additional text.
The JSON must contain exactly these fields:
- meeting_outcome: string, 3-5 sentences.
- relationship_update: string, 2-3 sentences.
- relationship_tier: string, one of: Active Prospect, Warm Lead, Strategic Watch, Referral Source, Vendor, Advisory, No Further Action.
- contact_profile: string, 2-3 sentences.
- key_decisions: array of strings.
- open_items: array of strings.
- strategic_notes: string, 2-4 sentences.
- follow_up_cadence: string.
- draft_email: string. Complete draft follow-up email. Max 150 words. Subject formatted as: SUBJECT: [subject line] then email body. Sign off as: Kevin Massengill, Chairman & CEO | Meraglim Holdings Corporation.
- action_items: array of objects each containing task (string), due_days (integer), priority (high/normal/low).

Do not wrap the response in markdown code blocks.
Return only the raw JSON object."""

INTERNAL_SYSTEM_PROMPT = """You are an executive meeting intelligence assistant. Analyze the meeting
transcript and return a JSON object with exactly these fields:
{
  "meeting_title": "brief descriptive title for this meeting",
  "attendees": "comma-separated list of attendees mentioned",
  "key_decisions": "summary of key decisions made",
  "next_steps": [
    {
      "task": "specific action item",
      "due_days": 7,
      "priority": "high"
    }
  ]
}
Priority must be: high, normal, or low.
due_days is an integer representing days from today.
Do not wrap the response in markdown code blocks.
Return only the raw JSON object."""


class GmailClient:
    def __init__(self, token_file: str):
        self.token_file = token_file
        self.service = self._get_service()
    
    def _get_service(self):
        try:
            creds = Credentials.from_authorized_user_file(self.token_file)
            return build("gmail", "v1", credentials=creds)
        except Exception as e:
            logger.error(f"Error initializing Gmail service: {str(e)}")
            raise
    
    def fetch_transcript_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        try:
            results = self.service.users().messages().list(
                userId="me",
                q='subject:TRANSCRIPT OR subject:INTERNAL is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get("messages", [])
            logger.info(f"Found {len(messages)} unread emails with TRANSCRIPT or INTERNAL")
            return messages
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise
    
    def get_attachment_data(self, message_id: str) -> tuple:
        try:
            msg = self.service.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()
            
            headers = msg["payload"].get("headers", [])
            # RFC 5322 header names are case-insensitive. Some MIME libraries
            # (e.g., Python email.mime via msg["subject"]=) emit lowercase
            # header names, which a strict == "Subject" check would miss.
            subject = next(
                (h["value"] for h in headers if h["name"].lower() == "subject"),
                "",
            )
            snippet = msg.get("snippet", "")
            
            attachment_data = None
            mime_type = None
            
            parts = msg["payload"].get("parts", [])
            for part in parts:
                if part.get("filename") and part["mimeType"] == "text/plain":
                    body = part.get("body", {})
                    if "attachmentId" in body:
                        att = self.service.users().messages().attachments().get(
                            userId="me", messageId=message_id,
                            id=body["attachmentId"]
                        ).execute()
                        attachment_data = base64.urlsafe_b64decode(att["data"]).decode("utf-8")
                        mime_type = part["mimeType"]
                        break
            
            return subject, snippet, attachment_data, mime_type
        except Exception as e:
            logger.error(f"Error getting attachment data: {str(e)}")
            return None, None, None, None
    
    def mark_as_read(self, message_id: str):
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
        except Exception as e:
            logger.error(f"Error marking email as read: {str(e)}")


class TranscriptProcessor:
    @staticmethod
    def clean_transcript(text: str) -> str:
        text = text.replace("--", "")
        text = text.replace(">", "")
        return text.strip()
    
    @staticmethod
    def extract_contact_name(subject: str) -> str:
        return subject.replace("TRANSCRIPT: ", "").strip()
    
    @staticmethod
    def extract_prospect_email(snippet: str, body: str) -> Optional[str]:
        pattern = r"PROSPECT_EMAIL:\s*([\w.+-]+@[\w-]+\.[\w.]+)"
        for text in [snippet, body]:
            if text:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip()
        return None


class AirtableClient:
    def __init__(self, api_key: str, base_id: str, table_id: str):
        self.api_key = api_key
        self.base_id = base_id
        self.table_id = table_id
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def search_prospect_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_id}"
            params = {
                "filterByFormula": f'{{Email}}="{email}"',
                "maxRecords": 10
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            records = response.json().get("records", [])
            if records:
                logger.info(f"Found Airtable record for {email}")
                return records[0]
            else:
                logger.info(f"No Airtable record found for {email}")
                return None
        except Exception as e:
            logger.error(f"Error searching Airtable: {str(e)}")
            return None
    
    def update_prospect_record(self, record_id: str, claude_data: Dict[str, Any]):
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            ai_notes_lines = [
                f"Meeting Outcome: {claude_data.get('meeting_outcome', '')}",
                f"Relationship Update: {claude_data.get('relationship_update', '')}",
                f"Key Decisions: {', '.join(claude_data.get('key_decisions', []))}",
                f"Open Items: {', '.join(claude_data.get('open_items', []))}"
            ]
            ai_notes = "\n\n".join(ai_notes_lines)
            
            fields = {
                "fld9OHxvSb9CQBVFy": "Meeting — transcript processed",
                "fldCwvDhZ7Pq0Bag0": today_str,
                "fldEutPEYYSKs32g1": today_str,
                "fldWbD5gQgUfw5Bbp": claude_data.get("relationship_tier", ""),
                "fldbKdp6x3LI8UDfi": claude_data.get("follow_up_cadence", ""),
                "fldeBBJuAesPWjqWq": claude_data.get("contact_profile", ""),
                "fldlTKzymOXMl7RWF": ai_notes
            }
            
            url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_id}/{record_id}"
            response = requests.patch(
                url,
                headers=self.headers,
                json={"fields": fields}
            )
            response.raise_for_status()
            logger.info(f"Updated Airtable record {record_id}")
        except Exception as e:
            logger.error(f"Error updating Airtable record: {str(e)}")


class ClickUpClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    
    def extract_clickup_task_id(self, airtable_record: Dict[str, Any]) -> Optional[str]:
        try:
            clickup_url = airtable_record.get("fields", {}).get("ClickUp Doc URL", "")
            if not clickup_url:
                return None
            return clickup_url.rstrip("/").split("/")[-1]
        except Exception as e:
            logger.error(f"Error extracting ClickUp task ID: {str(e)}")
            return None
    
    def post_comment(self, task_id: str, claude_data: Dict[str, Any]):
        try:
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            key_decisions_str = " | ".join(claude_data.get("key_decisions", []))
            open_items_str = " | ".join(claude_data.get("open_items", []))
            
            comment_lines = [
                f"POST-MEETING INTELLIGENCE — {date_str}",
                "",
                "=" * 32 + "\nMEETING OUTCOME\n" + "=" * 32,
                claude_data.get("meeting_outcome", ""),
                "",
                "=" * 32 + "\nCONTACT PROFILE\n" + "=" * 32,
                claude_data.get("contact_profile", ""),
                f"Relationship Tier: {claude_data.get('relationship_tier', '')}",
                "",
                "=" * 32 + "\nRELATIONSHIP UPDATE\n" + "=" * 32,
                claude_data.get("relationship_update", ""),
                "",
                "=" * 32 + "\nKEY DECISIONS\n" + "=" * 32,
                key_decisions_str,
                "",
                "=" * 32 + "\nOPEN ITEMS\n" + "=" * 32,
                open_items_str,
                "",
                "=" * 32 + "\nSTRATEGIC NOTES\n" + "=" * 32,
                claude_data.get("strategic_notes", ""),
                "",
                "=" * 32 + "\nFOLLOW-UP CADENCE\n" + "=" * 32,
                claude_data.get("follow_up_cadence", ""),
                "",
                "=" * 32 + "\nDRAFT FOLLOW-UP EMAIL\n" + "=" * 32,
                claude_data.get("draft_email", ""),
                "",
                "=" * 32 + "\nACTION ITEMS\n" + "=" * 32,
                "See Next Actions list in ClickUp — tasks created automatically."
            ]
            comment = "\n".join(comment_lines)
            
            url = f"https://api.clickup.com/api/v2/task/{task_id}/comment"
            response = requests.post(
                url,
                headers=self.headers,
                json={"comment_text": comment, "notify_all": False}
            )
            response.raise_for_status()
            logger.info(f"Posted ClickUp comment on task {task_id}")
        except Exception as e:
            logger.error(f"Error posting ClickUp comment: {str(e)}")
    
    def create_next_action_task(self, item: Dict[str, Any], prospect_email: Optional[str] = None):
        try:
            due = datetime.now() + timedelta(days=item.get("due_days", 7))
            due_ms = int(due.timestamp() * 1000)
            
            custom_fields = []
            if prospect_email:
                custom_fields.append({
                    "id": CLICKUP_PROSPECT_EMAIL_FIELD_ID,
                    "value": prospect_email
                })
            
            payload = {
                "name": item.get("task", ""),
                "due_date": due_ms,
                "due_date_time": False,
                "priority": self._map_priority(item.get("priority", "normal")),
                "notify_all": False,
                "custom_fields": custom_fields
            }
            
            url = f"https://api.clickup.com/api/v2/list/{CLICKUP_NEXT_ACTIONS_LIST_ID}/task"
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Created Next Action task: {item.get('task', '')}")
        except Exception as e:
            logger.error(f"Error creating ClickUp task: {str(e)}")
    
    def create_meeting_summary_task(self, claude_data: Dict[str, Any]) -> Optional[str]:
        try:
            now = datetime.now()
            due_ms = int(now.timestamp() * 1000)
            
            custom_fields = [
                {
                    "id": "68f58d6b-f9b3-4dd1-b9dc-a85852b61a5f",
                    "value": due_ms
                },
                {
                    "id": "78d9e9fc-03d1-4a85-8b56-1ae106aa0a1c",
                    "value": " | ".join([s.get("task", "") for s in claude_data.get("next_steps", [])])
                },
                {
                    "id": "aeafe808-2256-4758-a847-db25618929ea",
                    "value": claude_data.get("key_decisions", "")
                },
                {
                    "id": "d0c9b4b2-daf7-4638-99df-ea7aac0ccfa5",
                    "value": claude_data.get("attendees", "")
                }
            ]
            
            payload = {
                "name": claude_data.get("meeting_title", "Internal Meeting"),
                "due_date": due_ms,
                "due_date_time": False,
                "priority": 2,
                "notify_all": False,
                "custom_fields": custom_fields
            }
            
            url = f"https://api.clickup.com/api/v2/list/{CLICKUP_MEETING_SUMMARIES_LIST_ID}/task"
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data.get("id")
            logger.info(f"Created Meeting Summary task: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Error creating Meeting Summary task: {str(e)}")
            return None
    
    def create_internal_next_step(self, step: Dict[str, Any]):
        try:
            due = datetime.now() + timedelta(days=step.get("due_days", 7))
            due_ms = int(due.timestamp() * 1000)
            
            payload = {
                "name": step.get("task", ""),
                "due_date": due_ms,
                "due_date_time": False,
                "priority": self._map_priority(step.get("priority", "normal")),
                "notify_all": False
            }
            
            url = f"https://api.clickup.com/api/v2/list/{CLICKUP_NEXT_ACTIONS_LIST_ID}/task"
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Created internal Next Step task: {step.get('task', '')}")
        except Exception as e:
            logger.error(f"Error creating internal Next Step task: {str(e)}")
    
    @staticmethod
    def _map_priority(priority_str: str) -> int:
        priority_map = {"high": 3, "normal": 2, "low": 1}
        return priority_map.get(priority_str.lower(), 2)


class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def analyze_transcript(self, system_prompt: str, transcript: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": transcript}]
            )
            
            raw = response.content[0].text
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            
            data = json.loads(raw)
            logger.info("Successfully analyzed transcript with Claude")
            return data
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return None


@handle_errors(SCRIPT_NAME, logger)
def main():
    logger.info(f"Starting {SCRIPT_NAME}")
    
    try:
        gmail = GmailClient(GOOGLE_TOKEN_FILE)
        airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)
        clickup = ClickUpClient(CLICKUP_API_KEY)
        claude = ClaudeClient(ANTHROPIC_API_KEY)
        
        emails = gmail.fetch_transcript_emails(max_results=10)
        
        if not emails:
            logger.info("No unread emails to process")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        processed_count = 0
        
        for email in emails:
            message_id = email["id"]
            
            subject, snippet, attachment_data, mime_type = gmail.get_attachment_data(message_id)
            
            if mime_type != "text/plain":
                logger.info(f"Skipping {message_id}: attachment is {mime_type}, not text/plain")
                gmail.mark_as_read(message_id)
                continue
            
            transcript = TranscriptProcessor.clean_transcript(attachment_data)
            
            if "TRANSCRIPT" in subject:
                logger.info(f"Processing EXTERNAL path for: {subject}")
                
                contact_name = TranscriptProcessor.extract_contact_name(subject)
                prospect_email = TranscriptProcessor.extract_prospect_email(snippet, attachment_data)
                
                logger.info(f"Contact: {contact_name}, Email: {prospect_email}")
                
                claude_data = claude.analyze_transcript(EXTERNAL_SYSTEM_PROMPT, transcript)
                if not claude_data:
                    gmail.mark_as_read(message_id)
                    continue
                
                record = None
                task_id = None
                if prospect_email:
                    record = airtable.search_prospect_by_email(prospect_email)
                    if record:
                        task_id = clickup.extract_clickup_task_id(record)
                        airtable.update_prospect_record(record["id"], claude_data)
                        if task_id:
                            clickup.post_comment(task_id, claude_data)
                
                for item in claude_data.get("action_items", []):
                    clickup.create_next_action_task(item, prospect_email or "")
                
                processed_count += 1
            
            elif "INTERNAL" in subject:
                logger.info(f"Processing INTERNAL path for: {subject}")
                
                claude_data = claude.analyze_transcript(INTERNAL_SYSTEM_PROMPT, transcript)
                if not claude_data:
                    gmail.mark_as_read(message_id)
                    continue
                
                summary_task_id = clickup.create_meeting_summary_task(claude_data)
                
                for step in claude_data.get("next_steps", []):
                    clickup.create_internal_next_step(step)
                
                processed_count += 1
            
            else:
                logger.info(f"No matching route for subject: {subject}")
            
            gmail.mark_as_read(message_id)
            
            state_manager.update_state(
                SCRIPT_NAME,
                last_processed_id=message_id,
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
