# Script 3: Qualified Prospect - Calendar Invite
## Complete Deployment Documentation

**Project**: Make.com Migration - Local Automations  
**Date**: March 23, 2026  
**Status**: ✅ PRODUCTION READY  

---

## Table of Contents

1. Executive Summary
2. What It Does
3. Configuration
4. Files Created
5. LaunchAgent Setup
6. Manual Testing
7. Email Template
8. Troubleshooting
9. Key Lessons Learned
10. Monitoring
11. Quick Reference Commands
12. Testing Workflow

---

## Executive Summary

**Script 3** monitors the Airtable Prospects table for qualified prospects and automatically sends personalized calendar invite emails via Gmail OAuth. It runs every 15 minutes via macOS LaunchAgent.

### ✅ What Was Accomplished

✅ Created Python script that monitors Airtable Prospects table
✅ Implemented Gmail OAuth 2.0 authentication (not SMTP)
✅ Set up three-condition filter (Email + In Automation + Status = Qualified)
✅ Configured automatic Airtable record updates (2 fields)
✅ Implemented safeguards against mass mailings (MAX_EMAILS_PER_RUN = 1)
✅ Added SQLite state tracking to prevent duplicate emails
✅ Fixed email HTML formatting (Times New Roman, proper line breaks)
✅ Created LaunchAgent plist for 15-minute recurring execution
✅ Comprehensive logging to ~/Automations/logs/
✅ Created detailed documentation and quick reference guides

---

## What It Does

1. **Monitors Airtable** for prospects matching three criteria:
   - Email field is not blank
   - In Automation = TRUE (checked)
   - Qualification Status = "Qualified"

2. **Sends Calendar Invite Email** via Gmail OAuth with:
   - Personalized greeting (First Name)
   - Company-specific subject line
   - HubSpot calendar link
   - Professional signature (Times New Roman font)

3. **Updates Airtable** with:
   - Date Sent (timestamp)
   - Qualification Status → "Meeting Invite Sent"

4. **Prevents Duplicates** via SQLite state tracking database

5. **Logs Everything** to ~/Automations/logs/script_03_qualified_prospect_calendar_invite.log

---

## Configuration

### Airtable
- **Base ID**: appoNkgoKHAUXgXV9
- **Table ID**: tblxEhVek8ldTQMW1
- **Filter Formula**: `AND({Qualification Status} = 'Qualified', NOT({Email} = BLANK()), {In Automation} = TRUE())`

### Field IDs
| Field Name | Field ID |
|-----------|----------|
| Email | (standard field) |
| In Automation | (standard field) |
| Qualification Status | (standard field) |
| Date Sent | fldI2tIVJyDy1Cymi |
| Qualification Status (update) | fldgCH6CyIsNUCkV8 |

### Gmail OAuth
- **Method**: Google OAuth 2.0 (not SMTP)
- **Credentials File**: ~/Automations/config/oauth_credentials.json
- **Token File**: ~/Automations/config/oauth_token.json
- **Scope**: gmail.send

### Safeguards
- **DRY_RUN**: False (set to True to test without sending)
- **MAX_EMAILS_PER_RUN**: 1 (prevents mass mailings)
- **Email Validation**: Regex check for valid format
- **State Tracking**: SQLite database at ~/Automations/config/state.db

---

## Files Created

| File | Purpose |
|------|---------|
| ~/Automations/scripts/script_03_qualified_prospect_calendar_invite_oauth.py | Main script |
| ~/Automations/config/oauth_credentials.json | Gmail OAuth credentials |
| ~/Automations/config/oauth_token.json | Gmail OAuth token (auto-generated) |
| ~/Automations/config/state.db | SQLite database tracking processed records |
| ~/Automations/logs/script_03_qualified_prospect_calendar_invite.log | Execution log |
| ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist | LaunchAgent configuration |

---

## LaunchAgent Setup

### Start the Service
```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist
```

### Check Status
```bash
launchctl list | grep com.meraglim.script_03_qualified_prospect_calendar_invite
```

Expected output: `- 0 com.meraglim.script_03_qualified_prospect_calendar_invite`

### Stop the Service
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist
```

### Restart the Service
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist
launchctl load ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist
```

### View Logs
```bash
# Main execution log
tail -f ~/Automations/logs/script_03_qualified_prospect_calendar_invite.log

# LaunchAgent output
tail -f ~/Automations/logs/script_03_launchagent.log

# LaunchAgent errors
tail -f ~/Automations/logs/script_03_launchagent_error.log
```

---

## Manual Testing

### Test with Dry Run (No Emails Sent)
1. Edit the script and set `DRY_RUN = True`
2. Run: `/usr/bin/python3 ~/Automations/scripts/script_03_qualified_prospect_calendar_invite_oauth.py`
3. Check logs to verify it would send emails
4. Set `DRY_RUN = False` when ready

### Test with Real Email
1. Create a test prospect in Airtable with:
   - Email: your test email
   - In Automation: checked
   - Qualification Status: "Qualified"
2. Clear state database: `rm ~/Automations/config/state.db`
3. Run script: `/usr/bin/python3 ~/Automations/scripts/script_03_qualified_prospect_calendar_invite_oauth.py`
4. Check your email for the calendar invite email
5. Verify Airtable record was updated

### Reset a Prospect
To resend an email to a prospect:
1. In Airtable, set Qualification Status back to "Qualified"
2. Clear state database: `rm ~/Automations/config/state.db`
3. Run script again

---

## Email Template

### Subject Line
```
Let's schedule time - [Company Name]
```

### Body
- Personalized greeting with first name
- Confirmation of interest
- Description of next steps (30-minute call)
- Explanation of 10-year payment structure and tax advantages
- Calendar link: https://meetings.hubspot.com/kmassengill
- Professional closing
- Signature with name, title, company, and email

### Font
Times New Roman, 14px

---

## Troubleshooting

### Script Not Running
1. Check LaunchAgent status: `launchctl list | grep com.meraglim.script_03_qualified_prospect_calendar_invite`
2. Check error logs: `tail -f ~/Automations/logs/script_03_launchagent_error.log`
3. Verify plist file exists: `ls -la ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist`

### No Emails Being Sent
1. Check if prospects match filter criteria (Email, In Automation, Status = "Qualified")
2. Check logs: `tail -f ~/Automations/logs/script_03_qualified_prospect_calendar_invite.log`
3. Verify Gmail OAuth token is valid: `cat ~/Automations/config/oauth_token.json`
4. Run manual test with dry run enabled

### Duplicate Emails Sent
1. State database may be corrupted
2. Clear it: `rm ~/Automations/config/state.db`
3. Restart script: `launchctl unload ... && launchctl load ...`

### Gmail OAuth Token Expired
1. Delete token file: `rm ~/Automations/config/oauth_token.json`
2. Run script manually to re-authenticate
3. Follow the browser login flow

---

## Key Lessons Learned

### 1. Always Test Before Production
- **Protocol**: Create test prospect → verify email format → check Airtable updates → then deploy

### 2. Email Formatting in Gmail
- **Solution**: Use separate `<p>` tags with `margin: 0; padding: 0;` for each line
- **Best Practice**: Wrap signature in individual `<p>` tags for proper line breaks

### 3. Safeguards Against Mass Mailings
- **MAX_EMAILS_PER_RUN = 1**: Only sends one email per execution
- **DRY_RUN mode**: Test without actually sending
- **Email validation**: Check format before sending
- **State tracking**: SQLite database prevents duplicates

### 4. Filter Formula Syntax
- **Solution**: Use `AND({Qualification Status} = 'Qualified', NOT({Email} = BLANK()), {In Automation} = TRUE())`
- **Note**: Three conditions must ALL be true (Email exists AND In Automation AND Status = Qualified)

### 5. LaunchAgent vs Cron
- **LaunchAgent**: macOS native scheduler (preferred for Mac)
- **StartInterval**: 900 seconds = 15 minutes
- **RunAtLoad**: true = starts automatically on login
- **Logs**: StandardOutPath and StandardErrorPath capture all output

---

## Monitoring

### Daily Checks
1. Check logs for errors: `tail -20 ~/Automations/logs/script_03_qualified_prospect_calendar_invite.log`
2. Verify LaunchAgent is running: `launchctl list | grep com.meraglim.script_03_qualified_prospect_calendar_invite`
3. Check Airtable for updated records

### Weekly Review
1. Count emails sent (check logs)
2. Review any errors or failures
3. Verify Airtable updates are correct

### Monthly Maintenance
1. Archive old logs
2. Review and update email template if needed
3. Check Gmail OAuth token expiration

---

## Quick Reference Commands

### Essential Commands

**Check if running**:
```bash
launchctl list | grep com.meraglim.script_03_qualified_prospect_calendar_invite
```

**View live logs**:
```bash
tail -f ~/Automations/logs/script_03_qualified_prospect_calendar_invite.log
```

**Stop script**:
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist
```

**Start script**:
```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist
```

**Restart script**:
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist && launchctl load ~/Library/LaunchAgents/com.meraglim.script_03_qualified_prospect_calendar_invite.plist
```

**Run manually**:
```bash
/usr/bin/python3 ~/Automations/scripts/script_03_qualified_prospect_calendar_invite_oauth.py
```

**Clear state (reset processed records)**:
```bash
rm ~/Automations/config/state.db
```

**Reset Gmail OAuth**:
```bash
rm ~/Automations/config/oauth_token.json
```

---

## Testing Workflow (Detailed)

### 1. Create Test Prospect in Airtable
- First Name: "Test"
- Email: your email
- In Automation: checked
- Qualification Status: "Qualified"

### 2. Clear State Database
```bash
rm ~/Automations/config/state.db
```

### 3. Run Script
```bash
/usr/bin/python3 ~/Automations/scripts/script_03_qualified_prospect_calendar_invite_oauth.py
```

### 4. Check Email
- Look for email from kmassengill@meraglim.com
- Verify formatting (Times New Roman, proper line breaks)
- Check subject line includes company name
- Verify HubSpot calendar link works

### 5. Verify Airtable Updates
- Date Sent: timestamp
- Qualification Status: "Meeting Invite Sent"
