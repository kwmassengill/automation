#!/usr/bin/env python3
"""
Script 8: Meeting Scheduled Trigger

Wrapper script that triggers Script 10 for prospects with "Meeting Scheduled" status.

Trigger: Records in Airtable with Qualification Status = "Meeting Scheduled"
Actions:
  1. Find prospects with Meeting Scheduled status and no pre-meeting intelligence yet
  2. Call Script 10 with each prospect's email address

Schedule: Every 5 minutes via cron (or manually triggered)
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for shared utilities
sys.path.insert(0, str(Path(__file__).parent))

from shared_utils import setup_logger, StateManager, send_error_notification, handle_errors, load_credentials

# Third-party imports
import requests

# Load credentials
creds = load_credentials()

# Configuration
SCRIPT_NAME = "script_08_meeting_scheduled_trigger"
AIRTABLE_API_KEY = creds["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = creds["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"  # Prospects table

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


def get_scheduled_meetings_without_prep() -> List[Dict[str, Any]]:
    """Get prospects with Meeting Scheduled status that don't have prep summaries yet."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    # Filter for records where Qualification Status = "Meeting Scheduled" and Meeting Prep Summary is empty
    filter_formula = "AND({Qualification Status} = 'Meeting Scheduled', {Meeting Prep Summary} = BLANK())"
    
    try:
        records = airtable.get_records(AIRTABLE_TABLE_ID, filter_formula)
        logger.info(f"Found {len(records)} prospects with scheduled meetings needing prep")
        return records
    
    except Exception as e:
        logger.error(f"Error getting scheduled meetings: {str(e)}")
        raise


def call_script_10(prospect_email: str) -> bool:
    """Call Script 10 with prospect email."""
    try:
        script_10_path = Path(__file__).parent / "script_10_pre_meeting_intelligence.py"
        
        result = subprocess.run(
            [sys.executable, str(script_10_path), prospect_email],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Script 10 completed successfully for {prospect_email}")
            return True
        else:
            logger.error(f"Script 10 failed for {prospect_email}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        logger.error(f"Script 10 timed out for {prospect_email}")
        return False
    except Exception as e:
        logger.error(f"Error calling Script 10: {str(e)}")
        return False


@handle_errors(SCRIPT_NAME, logger)
def main():
    """Main execution function."""
    logger.info(f"Starting {SCRIPT_NAME}")
    
    try:
        # Get prospects with scheduled meetings
        prospects = get_scheduled_meetings_without_prep()
        
        if not prospects:
            logger.info("No prospects with scheduled meetings needing prep")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        # Process each prospect
        processed_count = 0
        for prospect in prospects:
            prospect_id = prospect["id"]
            fields = prospect.get("fields", {})
            prospect_email = fields.get("Email", "")
            prospect_name = fields.get("Name", "Unknown")
            
            if not prospect_email:
                logger.warning(f"Prospect {prospect_name} has no email, skipping")
                continue
            
            logger.info(f"Triggering Script 10 for: {prospect_name} ({prospect_email})")
            
            # Call Script 10
            if call_script_10(prospect_email):
                processed_count += 1
                # Update state
                state_manager.update_state(
                    SCRIPT_NAME,
                    last_processed_id=prospect_id,
                    last_processed_timestamp=datetime.now().isoformat(),
                    status="success"
                )
        
        logger.info(f"Successfully triggered Script 10 for {processed_count}/{len(prospects)} prospects")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error triggering Script 10: {str(e)}",
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
