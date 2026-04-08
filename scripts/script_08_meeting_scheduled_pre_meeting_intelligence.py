#!/usr/bin/env python3
"""
Script 8: Meeting Scheduled → Pre-Meeting Intelligence (Claude)

Watches for prospects with "Meeting Scheduled" status and generates
pre-meeting intelligence using Claude AI.

Trigger: Records in Airtable with Qualification Status = "Meeting Scheduled"
Actions:
  1. Check for prospects with Meeting Scheduled status
  2. Generate pre-meeting intelligence using Claude AI
  3. Store results in Airtable Meeting Prep Summary field

Schedule: Every 5 minutes via cron (or manually triggered)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for shared utilities
sys.path.insert(0, str(Path(__file__).parent))

from shared_utils import setup_logger, StateManager, send_error_notification, handle_errors, load_credentials

# Third-party imports
import requests
import anthropic

# Load credentials
creds = load_credentials()

# Configuration
SCRIPT_NAME = "script_08_meeting_scheduled_pre_meeting_intelligence"
AIRTABLE_API_KEY = creds["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = creds["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"  # Prospects table

CLAUDE_API_KEY = creds.get("CLAUDE_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

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


class ClaudeIntelligenceGenerator:
    """Generate pre-meeting intelligence using Claude AI."""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def generate_meeting_prep(self, prospect_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate pre-meeting intelligence for a prospect using Claude.
        
        Args:
            prospect_data: Prospect information from Airtable
        
        Returns:
            Pre-meeting intelligence summary or None if generation fails
        """
        try:
            # Extract prospect information
            name = prospect_data.get("Name", "Unknown")
            company = prospect_data.get("Company", "Unknown")
            title = prospect_data.get("Title", "")
            email = prospect_data.get("Email", "")
            sector = prospect_data.get("Sector", "")
            revenue = prospect_data.get("Estimated Revenue", "")
            ebitda = prospect_data.get("EBITDA Normalized", "")
            key_risk = prospect_data.get("Key Risk", "")
            ai_analysis = prospect_data.get("AI Analysis Notes", "")
            
            # Build the prompt for Claude
            prompt = f"""You are a business development expert preparing for a meeting with a prospect.

PROSPECT INFORMATION:
- Name: {name}
- Title: {title}
- Company: {company}
- Email: {email}
- Sector: {sector}
- Estimated Revenue: {revenue}
- EBITDA: {ebitda}
- Key Risk: {key_risk}
- AI Analysis Notes: {ai_analysis}

Generate a comprehensive pre-meeting intelligence brief that includes:

1. **Company Overview**: Brief context about the company and industry
2. **Key Discussion Points**: 3-5 specific topics to discuss based on their profile
3. **Pain Points to Address**: Likely challenges they face (based on sector, revenue, EBITDA)
4. **Value Proposition**: How your services align with their needs
5. **Questions to Ask**: 3-4 strategic questions to understand their situation better
6. **Meeting Strategy**: Recommended approach and tone for the meeting
7. **Red Flags to Watch**: Any concerns or areas to be cautious about

Format the response as a clear, actionable brief that can be reviewed before the meeting.
Keep it concise but comprehensive (300-500 words)."""
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the response
            intelligence = message.content[0].text
            logger.info(f"Generated pre-meeting intelligence for {name}")
            return intelligence
        
        except Exception as e:
            logger.error(f"Error generating meeting intelligence: {str(e)}")
            return None


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


def update_meeting_prep(prospect_id: str, prep_summary: str) -> bool:
    """Update prospect record with pre-meeting intelligence."""
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    
    fields = {
        "Meeting Prep Summary": prep_summary,
        "Last Briefed": datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        airtable.update_record(AIRTABLE_TABLE_ID, prospect_id, fields)
        return True
    except Exception as e:
        logger.error(f"Error updating meeting prep: {str(e)}")
        return False


@handle_errors(SCRIPT_NAME, logger)
def main():
    """Main execution function."""
    logger.info(f"Starting {SCRIPT_NAME}")
    
    try:
        # Check if Claude API key is configured
        if not CLAUDE_API_KEY or CLAUDE_API_KEY.startswith("<"):
            logger.warning("Claude API key not configured. Skipping execution.")
            logger.info("To configure: Set CLAUDE_API_KEY in .env file")
            return
        
        # Get prospects with scheduled meetings
        prospects = get_scheduled_meetings_without_prep()
        
        if not prospects:
            logger.info("No prospects with scheduled meetings needing prep")
            state_manager.update_state(SCRIPT_NAME, status="success")
            return
        
        # Initialize Claude intelligence generator
        claude = ClaudeIntelligenceGenerator(CLAUDE_API_KEY, CLAUDE_MODEL)
        
        # Process each prospect
        processed_count = 0
        for prospect in prospects:
            prospect_id = prospect["id"]
            fields = prospect.get("fields", {})
            prospect_name = fields.get("Name", "Unknown")
            
            logger.info(f"Generating pre-meeting intelligence for: {prospect_name}")
            
            # Generate pre-meeting intelligence
            prep_summary = claude.generate_meeting_prep(fields)
            
            if prep_summary:
                # Update Airtable record
                if update_meeting_prep(prospect_id, prep_summary):
                    processed_count += 1
                    # Update state
                    state_manager.update_state(
                        SCRIPT_NAME,
                        last_processed_id=prospect_id,
                        last_processed_timestamp=datetime.now().isoformat(),
                        status="success"
                    )
        
        logger.info(f"Successfully generated {processed_count}/{len(prospects)} pre-meeting briefs")
        state_manager.update_state(SCRIPT_NAME, status="success")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        state_manager.increment_error_count(SCRIPT_NAME)
        send_error_notification(
            SCRIPT_NAME,
            f"Error generating pre-meeting intelligence: {str(e)}",
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
