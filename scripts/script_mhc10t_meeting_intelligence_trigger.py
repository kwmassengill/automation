#!/usr/bin/env python3
"""
Script MHC-10T: Meeting Intelligence Trigger

Watches for calendar events and triggers meeting intelligence processing.
Stores event data for later processing by other scripts.

Trigger: New calendar events in Google Calendar
Actions:
  1. Check for new calendar events
  2. Store event data in local datastore
  3. Send event data to external meeting intelligence service

Schedule: Every 5 minutes via cron (during business hours)
"""

import os
import sys
import json
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

# Load environment variables
load_dotenv()

# Configuration
SCRIPT_NAME = "script_mhc10t_meeting_intelligence_trigger"
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "/Users/kevinmassengill/Automations/config/google_token.json")

# External meeting intelligence service
MEETING_INTELLIGENCE_WEBHOOK = os.getenv("MAKE_WEBHOOK_BASE_URL", "https://hook.make.com") + "/meeting-intelligence"

# Initialize logger and state manager
logger = setup_logger(SCRIPT_NAME)
state_manager = StateManager()


class GoogleCalendarClient:
    """Client for Google Calendar API operations."""
    
    def __init__(self, token_file: str):
        self.token_file = token_file
        self.service = self._get_service()
    
    def _get_service(self):
        """Get Google Calendar service."""
        try:
            creds = Credentials.from_authorized_user_file(self.token_file)
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Error initializing Google Calendar service: {str(e)}")
            raise
    
    def get_upcoming_events(self, minutes_ahead: int = 60, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming calendar events."""
        try:
            now = datetime.utcnow().isoformat() + "Z"
            later = (datetime.utcnow() + timedelta(minutes=minutes_ahead)).isoformat() + "Z"
            
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=now,
                timeMax=later,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = events_result.get("items", [])
            logger.info(f"Found {len(events)} upcoming events")
            return events
        
        except Exception as e:
            logger.error(f"Error getting calendar events: {str(e)}")
            raise
    
    def get_event_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a calendar event."""
        try:
            event = self.service.events().get(
                calendarId="primary",
                eventId=event_id
            ).execute()
            return event
        except Exception as e:
            logger.error(f"Error getting event details: {str(e)}")
            return None


class DataStore:
    """Simple local datastore for meeting events."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or os.getenv("STATE_DB_PATH", "/Users/kevinmassengill/Automations/config/state.db"))
        self.json_file = self.db_path.parent / "meeting_events.json"
        self._init_store()
    
    def _init_store(self):
        """Initialize the JSON store."""
        if not self.json_file.exists():
            with open(self.json_file, "w") as f:
                json.dump({"events": []}, f)
    
    def add_event(self, event: Dict[str, Any]) -> bool:
        """Add an event to the datastore."""
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
            
            # Check if event already exists
            if any(e["id"] == event["id"] for e in data["events"]):
                logger.info(f"Event {event['id']} already in store")
                return False
            
            data["events"].append(event)
            
            with open(self.json_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Added event {event['id']} to datastore")
            return True
        except Exception as e:
            logger.error(f"Error adding event to datastore: {str(e)}")
            return False
    
    def get_unprocessed_events(self) -> List[Dict[str, Any]]:
        """Get events that haven't been processed yet."""
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
            
            unprocessed = [e for e in data["events"] if not e.get("processed")]
            return unprocessed
        except Exception as e:
            logger.error(f"Error getting unprocessed events: {str(e)}")
            return []
    
    def mark_event_processed(self, event_id: str) -> bool:
        """Mark an event as processed."""
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
            
            for event in data["events"]:
                if event["id"] == event_id:
                    event["processed"] = True
                    event["processed_at"] = datetime.now().isoformat()
                    break
            
            with open(self.json_file, "w") as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error marking event as processed: {str(e)}")
            return False


def send_to_meeting_intelligence(event: Dict[str, Any]) -> bool:
    """Send event data to meeting intelligence service."""
    try:
        payload = {
            "event_id": event.get("id"),
            "summary": event.get("summary"),
            "description": event.get("description"),
            "start": event.get("start"),
            "end": event.get("end"),
            "attendees": event.get("attendees", []),
            "created_at": datetime.now().isoformat()
        }
        
        response = requests.post(
            MEETING_INTELLIGENCE_WEBHOOK,
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Sent event {event['id']} to meeting intelligence service")
            return True
        else:
            logger.warning(f"Meeting intelligence service returned {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"Error sending to meeting intelligence service: {str(e)}")
        return False


@handle_errors(SCRIPT_NAME, logger)
def main():
    """Main execution function."""
    logger.info(f"Starting {SCRIPT_NAME}")
    
    try:
        calendar = GoogleCalendarClient(GOOGLE_TOKEN_FILE)
        datastore = DataStore()
        
        # Get upcoming events
        events = calendar.get_upcoming_events(minutes_ahead=120, max_results=10)
        
        if not events:
            logger.info("No upcoming events")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        # Process each event
        processed_count = 0
        for event in events:
            event_id = event.get("id")
            summary = event.get("summary", "Untitled Event")
            
            logger.info(f"Processing event: {summary}")
            
            # Prepare event data
            event_data = {
                "id": event_id,
                "summary": summary,
                "description": event.get("description", ""),
                "start": event.get("start", {}),
                "end": event.get("end", {}),
                "attendees": event.get("attendees", []),
                "created_at": datetime.now().isoformat(),
                "processed": False
            }
            
            # Add to datastore
            if datastore.add_event(event_data):
                # Send to meeting intelligence service
                if send_to_meeting_intelligence(event_data):
                    datastore.mark_event_processed(event_id)
                    processed_count += 1
                    
                    # Update state
                    state_manager.update_state(
                        SCRIPT_NAME,
                        last_processed_id=event_id,
                        last_processed_timestamp=datetime.now().isoformat(),
                        status="success"
                    )
        
        logger.info(f"Successfully processed {processed_count}/{len(events)} events")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error processing calendar events: {str(e)}",
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
