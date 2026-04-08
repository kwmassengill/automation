# Script 5: Quick Reference Guide

## What it does
Sends a 7-day follow-up email to prospects who haven't responded to the initial qualification email.

## Where files live
- **Script**: `~/Automations/scripts/script_05_no_response_7_day_followup_oauth.py`
- **Logs**: `~/Automations/logs/script_05_no_response_7_day_followup.log`
- **Errors**: `~/Automations/logs/script_05_no_response_7_day_followup_error.log`
- **LaunchAgent**: `~/Library/LaunchAgents/com.meraglim.script05_no_response_7day_followup.plist`

## How to check if it's running
```bash
launchctl list | grep com.meraglim.script05
```

## How to view what it's doing right now
```bash
tail -f ~/Automations/logs/script_05_no_response_7_day_followup.log
```

## How to stop it
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script05_no_response_7day_followup.plist
```

## How to start it
```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script05_no_response_7day_followup.plist
```

## How to run it manually (for testing)
```bash
/usr/bin/python3 ~/Automations/scripts/script_05_no_response_7_day_followup_oauth.py
```

## Troubleshooting

**Problem: Emails aren't sending**
1. Check the logs: `tail -50 ~/Automations/logs/script_05_no_response_7_day_followup.log`
2. Look for OAuth errors. If the token expired, you may need to run the script manually once to re-authenticate via the browser.

**Problem: It's sending to the wrong people**
1. Check the Airtable filter formula in the script.
2. Verify the `Days Since Email` field in Airtable is calculating correctly.

**Problem: It's sending duplicate emails**
1. Check the state database: `sqlite3 ~/Automations/config/state.db "SELECT * FROM script_state WHERE script_name='script_05_no_response_7_day_followup';"`
2. Ensure the script is successfully updating the Airtable `Qualification Status` after sending.
