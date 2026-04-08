# Script 3: Quick Reference Guide

## Essential Commands

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

## Testing Workflow

**Step 1**: Create test prospect in Airtable (First Name: "Test", Email: your email, In Automation: checked, Status: "Qualified")

**Step 2**: Clear state database: `rm ~/Automations/config/state.db`

**Step 3**: Run script: `/usr/bin/python3 ~/Automations/scripts/script_03_qualified_prospect_calendar_invite_oauth.py`

**Step 4**: Check email for proper formatting (Times New Roman, line breaks, company name in subject, HubSpot link)

**Step 5**: Verify Airtable updates (Date Sent, Status)

## Configuration

- **Airtable Base ID**: appoNkgoKHAUXgXV9
- **Airtable Table ID**: tblxEhVek8ldTQMW1
- **Filter Formula**: `AND({Qualification Status} = 'Qualified', NOT({Email} = BLANK()), {In Automation} = TRUE())`
- **Schedule**: Every 15 minutes (900 seconds)
- **Safeguards**: MAX_EMAILS_PER_RUN = 1, DRY_RUN = False
