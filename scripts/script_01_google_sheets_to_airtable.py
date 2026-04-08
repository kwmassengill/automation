#!/usr/bin/env python3
import os, sys, json
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from shared_utils import setup_logger, StateManager, send_error_notification, handle_errors
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load .env file explicitly
env_file = Path.home() / "Automations" / "config" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

SCRIPT_NAME = "script_01_google_sheets_to_airtable"
GOOGLE_SHEETS_ID = "1NX2xxzkKUO-EY2QXO_OtHQTaqGV8dvbxXikGMBoeS-g"
GOOGLE_SHEET_NAME = "Leads"
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "/Users/kevinmassengill/Automations/config/google_token.json")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = "appoNkgoKHAUXgXV9"
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"
logger = setup_logger(SCRIPT_NAME)
state_manager = StateManager()

class GoogleSheetsClient:
    def __init__(self, token_file):
        self.token_file = token_file
        self.service = self._get_service()
    def _get_service(self):
        creds = Credentials.from_authorized_user_file(self.token_file)
        return build("sheets", "v4", credentials=creds)
    def get_rows(self, spreadsheet_id, sheet_name, start_row=2):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1:Z500",
            valueRenderOption="FORMATTED_VALUE",
            dateTimeRenderOption="FORMATTED_STRING"
        ).execute()
        values = result.get("values", [])
        return values[1:] if values else []  # Skip header row (row 1)

class AirtableClient:
    def __init__(self, api_key, base_id):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
    
    def record_exists_by_email(self, table_id, email ):
        url = f"{self.base_url}/{self.base_id}/{table_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"filterByFormula": f"{{Email}} = '{email}'"}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        records = response.json().get("records", [])
        return len(records) > 0
    
    def create_record(self, table_id, fields):
        url = f"{self.base_url}/{self.base_id}/{table_id}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json={"fields": fields})
        response.raise_for_status()
        record = response.json()
        logger.info(f"Created: {record['id']}")
        return record["id"]

def map_sheet_row_to_airtable(row):
    return {
        "First Name": row[1] if len(row) > 1 else "",
        "Last Name": row[2] if len(row) > 2 else "",
        "Email": row[3] if len(row) > 3 else "",
        "Company": row[4] if len(row) > 4 else "",
        "Title": row[5] if len(row) > 5 else "",
        "Lead Source": "Ever Outbound",
        "In Automation": True,
        "Qualification Status": "New"
    }

@handle_errors(SCRIPT_NAME, logger)
def main():
    logger.info(f"Starting {SCRIPT_NAME}")
    sheets = GoogleSheetsClient(GOOGLE_TOKEN_FILE)
    all_rows = sheets.get_rows(GOOGLE_SHEETS_ID, GOOGLE_SHEET_NAME)
    logger.info(f"Found {len(all_rows)} rows")
    
    if not all_rows:
        return
    
    state = state_manager.get_state(SCRIPT_NAME)
    last_processed_id = state.get("last_processed_id", "")
    
    if last_processed_id.startswith("row_"):
        last_row = int(last_processed_id.split("_")[1])
    else:
        last_row = -1
    
    logger.info(f"Last processed row: {last_row}")
    
    airtable = AirtableClient(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    created_count = 0
    skipped_count = 0
    
    for i in range(last_row + 1, len(all_rows)):
        row = all_rows[i]
        if not any(row):
            continue
        
        email = row[3] if len(row) > 3 else ""
        name = f"{row[1] if len(row) > 1 else ''} {row[2] if len(row) > 2 else ''}".strip()
        
        if not email:
            logger.warning(f"Row {i+2}: {name} - No email, skipping")
            skipped_count += 1
            continue
        
        if airtable.record_exists_by_email(AIRTABLE_TABLE_ID, email):
            logger.info(f"Row {i+2}: {name} ({email}) - Already exists, skipping")
            skipped_count += 1
            state_manager.update_state(SCRIPT_NAME, last_processed_id=f"row_{i}", last_processed_timestamp=datetime.now().isoformat(), status="success")
            continue
        
        logger.info(f"Processing row {i+2}: {name}")
        fields = map_sheet_row_to_airtable(row)
        record_id = airtable.create_record(AIRTABLE_TABLE_ID, fields)
        if record_id:
            created_count += 1
            state_manager.update_state(SCRIPT_NAME, last_processed_id=f"row_{i}", last_processed_timestamp=datetime.now().isoformat(), status="success")
    
    logger.info(f"Created {created_count} records, skipped {skipped_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal: {str(e)}", exc_info=True)
        sys.exit(1)
