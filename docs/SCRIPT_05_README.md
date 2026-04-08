# Script 5: No Response - 7 Day Follow Up

## Overview

This script automates the process of sending a follow-up email to prospects who received the initial qualification email exactly 7 days ago but have not yet responded. It uses Gmail OAuth 2.0 for secure email delivery and updates the prospect's status in Airtable.

**Status:** ✅ Ready for Production Deployment
**Trigger:** Every 15 minutes via LaunchAgent

## Key Features

1. **Precise Timing**: Uses Airtable's calculated `Days Since Email` field to find prospects exactly 7 days post-initial contact.
2. **Secure Email Delivery**: Uses Gmail OAuth 2.0 instead of basic SMTP for reliable, secure sending.
3. **Professional Formatting**: HTML email template uses `<p>` tags for perfect rendering in Gmail.
4. **State Tracking**: Uses SQLite database to prevent duplicate follow-ups to the same prospect.
5. **Safety First**: Implements `DRY_RUN` mode and `MAX_EMAILS_PER_RUN = 1` to prevent accidental mass mailings.

## Airtable Filter Logic

The script fetches prospects matching ALL of these conditions:
1. `Qualification Status` = "Qualification Email Sent"
2. `Email` is not blank
3. `In Automation` = True
4. `Date Sent` is not blank
5. `Days Since Email` >= 7

## Actions Performed

For each matching prospect, the script:
1. Sends the HTML follow-up email via Gmail OAuth.
2. Updates Airtable `Qualification Status` to "No Response - Followed Up".
3. Updates Airtable `Date Sent` to the current timestamp.
4. Records the successful action in the local SQLite state database.

## Deployment Instructions

### 1. File Placement
Place the following files in your `~/Automations` directory:
- `scripts/script_05_no_response_7_day_followup_oauth.py`
- `scripts/shared_utils.py` (Ensure this is up to date)

### 2. Configuration
Ensure your `~/Automations/config/.env` file contains:
```env
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=appoNkgoKHAUXgXV9
```

Ensure your Gmail OAuth credentials are in place:
- `~/Automations/config/oauth_credentials.json`
- `~/Automations/config/oauth_token.json`

### 3. Production Setup
Edit `script_05_no_response_7_day_followup_oauth.py`:
Change line 34 from:
```python
DRY_RUN = True
```
To:
```python
DRY_RUN = False
```

### 4. LaunchAgent Deployment
1. Copy the plist file to your LaunchAgents folder:
```bash
cp ~/Automations/config/com.meraglim.script05_no_response_7day_followup.plist ~/Library/LaunchAgents/
```

2. Load the LaunchAgent:
```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script05_no_response_7day_followup.plist
```

3. Verify it's loaded:
```bash
launchctl list | grep com.meraglim.script05
```

## Monitoring

Check the logs to ensure the script is running correctly:
```bash
tail -f ~/Automations/logs/script_05_no_response_7_day_followup.log
```

Check for errors:
```bash
tail -f ~/Automations/logs/script_05_no_response_7_day_followup_error.log
```
