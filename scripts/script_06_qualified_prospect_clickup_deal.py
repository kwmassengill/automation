#!/usr/bin/env python3
"""
Script 6: Qualified Prospect → ClickUp Deal Pipeline

Watches for qualified prospects in Airtable and creates a task in ClickUp deal pipeline.
Then updates the Airtable record to mark the task as created.

Trigger: Records in Airtable with "Status" = "Qualified"
Actions:
  1. Check for qualified prospects
  2. Create task in ClickUp deal pipeline
  3. Update Airtable record with ClickUp task link

Schedule: Every 5 minutes via cron
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

# Load credentials using centralized loader
from shared_utils import load_credentials
creds = load_credentials()

# Configuration
SCRIPT_NAME = "script_06_qualified_prospect_clickup_deal"
AIRTABLE_API_KEY = creds["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = creds["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"  # Prospects table

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
CLICKUP_TEAM_ID = os.getenv("CLICKUP_TEAM_ID")
CLICKUP_DEAL_LIST_ID = creds["CLICKUP_DEAL_LIST_ID"]

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


class ClickUpClient:
    """Client for ClickUp API operations."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    
    def create_task(self, list_id: str, name: str, description: str = "", 
                   priority: int = 2, due_date: Optional[str] = None,
                   custom_fields: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a task in ClickUp.
        
        Args:
            list_id: The ClickUp list ID
            name: Task name
            description: Task description
            priority: Priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            due_date: Due date in ISO format
            custom_fields: List of custom field dicts with "id" and "value" keys
        
        Returns:
            Task data if successful, None otherwise
        """
        url = f"{self.base_url}/list/{list_id}/task"
        
        data = {
            "name": name,
            "description": description,
            "priority": priority
        }
        
        if due_date:
            data["due_date"] = due_date
        
        if custom_fields:
            data["custom_fields"] = custom_fields
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            # ClickUp API v2 returns task data directly, not nested under "task" key
            task_id = response_json.get("id")
            task_url = response_json.get("url")
            logger.info(f"Created ClickUp task: {task_id} - {task_url}")
            return response_json
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating ClickUp task: {str(e)}")
            logger.error(f"Response status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
            logger.error(f"Response text: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            return None


def get_qualified_prospects_for_clickup() -> List[Dict[str, Any]]:
    """Get prospects from Airtable with Meeting Invite Sent status that need ClickUp tasks."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    # Filter for records where Status = "Meeting Invite Sent" and ClickUp Task NOT created
    filter_formula = "AND({Qualification Status} = 'Meeting Invite Sent', NOT({ClickUp Task Created}), NOT({Email} = BLANK()))"
    
    try:
        records = airtable.get_records(AIRTABLE_TABLE_ID, filter_formula)
        logger.info(f"Found {len(records)} qualified prospects without ClickUp tasks")
        return records
    
    except Exception as e:
        logger.error(f"Error getting qualified prospects: {str(e)}")
        raise


def create_clickup_task(prospect: Dict[str, Any]) -> Optional[str]:
    """Create a ClickUp task for a qualified prospect with custom fields populated."""
    clickup = ClickUpClient(CLICKUP_API_KEY)
    
    fields = prospect.get("fields", {})
    name = fields.get("Name", "Unknown Prospect")
    company = fields.get("Company", "")
    email = fields.get("Email", "")
    job_title = fields.get("Title", "")
    ebitda_range = fields.get("EBITDA Range Detected", "")
    payment_pref = fields.get("Payment Willingness Detected", "")
    lead_source = fields.get("Lead Source", "")
    qualification_notes = fields.get("AI Analysis Notes", "")
    
    task_name = f"Deal: {name} - {company}"
    task_description = f"""
Prospect Information:
- Name: {name}
- Company: {company}
- Email: {email}
- Job Title: {job_title}
- Airtable Record: {prospect['id']}

Next Steps:
1. Schedule initial meeting
2. Prepare proposal
3. Follow up on proposal
"""
    
    # Populate ClickUp custom fields from Airtable data
    custom_fields = [
        {"id": "04337311-ead6-45a8-9b7e-cb1446e277ae", "value": company},  # Company
        {"id": "fd825748-8018-4100-91a2-273dbf58087d", "value": name},  # Contact Name
        {"id": "b357b002-bcb7-41d1-8d3f-8421ea63a719", "value": email},  # Email
        {"id": "879d3b40-8730-4b92-b7f7-e70dfee08460", "value": ebitda_range},  # EBITDA Range
        {"id": "dfe75776-76f5-46ab-98f3-867bf7c323ad", "value": payment_pref},  # Payment Preference
        {"id": "c21ad178-d6ae-4aaa-8e83-c51554c003c9", "value": lead_source},  # Lead Source
        {"id": "8f14ec09-9b55-4a35-8d2c-e45e77754c18", "value": qualification_notes}  # Qualification Notes
    ]
    
    task = clickup.create_task(
        CLICKUP_DEAL_LIST_ID,
        task_name,
        task_description,
        priority=2,  # High priority
        custom_fields=custom_fields
    )
    
    if task and task.get("id"):
        return task
    return None


def update_prospect_status(prospect_id: str, task_id: str, task_url: str) -> bool:
    """Update prospect record with ClickUp task information."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    fields = {
        "ClickUp Task Created": True,
        "Deal Phase": "Pre-Qualification — Actively assessing against ABB criteria",
        "Deal Phase Date": datetime.now().strftime("%Y-%m-%d")
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
        # Check if ClickUp API key is configured
        if not CLICKUP_API_KEY or CLICKUP_API_KEY.startswith("<"):
            logger.warning("ClickUp API key not configured. Skipping execution.")
            logger.info("To configure: Set CLICKUP_API_KEY in .env file")
            return
        
        # Get qualified prospects
        prospects = get_qualified_prospects_for_clickup()
        
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
            
            # Create ClickUp task
            task = create_clickup_task(prospect )
            
            if task and task.get("id"):
                task_id = task.get("id")
                task_url = task.get("url")
                
                # Update Airtable record
                if update_prospect_status(prospect_id, task_id, task_url):
                    processed_count += 1
                    # Update state
                    state_manager.update_state(
                        SCRIPT_NAME,
                        last_processed_id=prospect_id,
                        last_processed_timestamp=datetime.now().isoformat(),
                        status="success"
                    )
        
        logger.info(f"Successfully created {processed_count}/{len(prospects)} ClickUp tasks")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error creating ClickUp tasks: {str(e)}",
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
