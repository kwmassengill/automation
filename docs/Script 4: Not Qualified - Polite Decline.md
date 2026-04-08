# Script 4: Not Qualified - Polite Decline

## Purpose
This script automates the process of sending a polite decline email to prospects who have been marked as "Not Qualified" in Airtable. It ensures that all unqualified prospects receive a professional response while saving time.

## Trigger
- **Schedule:** Runs every 15 minutes via macOS LaunchAgent
- **Condition:** Finds records in Airtable where:
  - `Qualification Status` = "Not Qualified"
  - `Email` is not blank
  - `In Automation` = TRUE

## Inputs & Outputs
- **Input:** Airtable Prospects table (Base: `appoNkgoKHAUXgXV9`, Table: `tblxEhVek8ldTQMW1`)
- **Output 1:** Sends an email via Gmail OAuth
- **Output 2:** Updates Airtable record:
  - Sets `Date Sent` to current time
  - Sets `Qualification Status` to "Declined Email Sent"

## Safeguards Implemented
1. **`MAX_EMAILS_PER_RUN = 1`**: Strictly limits the script to processing one prospect per execution to prevent mass emailing accidents.
2. **`DRY_RUN` Mode**: Available for testing without actually sending emails or updating Airtable.
3. **State Tracking**: Uses SQLite database to track processed records and prevent duplicate emails.
4. **Email Validation**: Checks email format before attempting to send.

## Deployment Instructions

### 1. Pre-Deployment Testing
Before deploying to production, follow these steps:

1. Create a test prospect in Airtable:
   - First Name: "Test"
   - Email: Your personal email address
   - Company: "Test Company"
   - In Automation: Checked
   - Qualification Status: "Not Qualified"

2. Run the script manually with `DRY_RUN = True` (edit the script file to set this):
   ```bash
   /usr/bin/python3 ~/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py
   ```

3. Verify the logs show what would happen without errors.

4. Set `DRY_RUN = False` and run manually again.

5. Verify:
   - You received the email and formatting looks correct
   - The Airtable record was updated correctly

### 2. Production Deployment

1. Move the script to the scripts directory:
   ```bash
   mv script_04_not_qualified_polite_decline_oauth.py ~/Automations/scripts/
   chmod +x ~/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py
   ```

2. Move the LaunchAgent plist to the correct directory:
   ```bash
   mv com.meraglim.script_04_not_qualified_polite_decline.plist ~/Library/LaunchAgents/
   ```

3. Load the LaunchAgent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.meraglim.script_04_not_qualified_polite_decline.plist
   ```

4. Verify it's loaded:
   ```bash
   launchctl list | grep com.meraglim.script_04
   ```

### 3. Monitoring

Monitor the logs for the first few executions:
```bash
tail -f ~/Automations/logs/script_04_not_qualified_polite_decline_*.log
```

Check for any LaunchAgent errors:
```bash
tail -f ~/Automations/logs/script_04_launchagent_error.log
```

## Troubleshooting

If the script fails to send emails:
1. Check if the Gmail OAuth token has expired. You may need to run the script manually to trigger the browser authentication flow.
2. Verify the Airtable API key and Base/Table IDs in the `.env` file.
3. Check the error logs for specific API errors.

To reset the state for a specific record (if you need to re-process it):
```bash
sqlite3 ~/Automations/config/state.db "DELETE FROM script_state WHERE script_name = 'script_04_not_qualified_polite_decline_RECORD_ID';"
```
