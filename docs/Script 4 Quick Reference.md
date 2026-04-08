# Script 4 Quick Reference

## Overview
Script 4 sends a polite decline email to prospects marked as "Not Qualified" in Airtable, then updates their record status.

## Key Files
- **Script:** `~/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py`
- **LaunchAgent:** `~/Library/LaunchAgents/com.meraglim.script_04_not_qualified_polite_decline.plist`
- **Logs:** `~/Automations/logs/script_04_*.log`
- **State DB:** `~/Automations/config/state.db`

## Quick Commands

### Check Status
```bash
launchctl list | grep com.meraglim.script_04
```

### View Logs
```bash
tail -f ~/Automations/logs/script_04_not_qualified_polite_decline_*.log
```

### Run Manually
```bash
/usr/bin/python3 ~/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py
```

### Load LaunchAgent
```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script_04_not_qualified_polite_decline.plist
```

### Unload LaunchAgent
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_04_not_qualified_polite_decline.plist
```

### Clear State (Reset Processing)
```bash
rm ~/Automations/config/state.db
```

## Configuration

### Safeguards
- `MAX_EMAILS_PER_RUN = 1` (prevents mass emailing)
- `DRY_RUN = False` (set to True for testing)

### Schedule
- Runs every 15 minutes (900 seconds)
- Configurable in plist file `StartInterval` key

### Airtable Filter
```
AND(
  {Qualification Status} = 'Not Qualified',
  NOT({Email} = BLANK()),
  {In Automation} = TRUE()
)
```

## Workflow

1. **Fetch** prospects from Airtable with status "Not Qualified"
2. **Check** if already processed (state tracking)
3. **Send** polite decline email via Gmail OAuth
4. **Update** Airtable record:
   - Set Date Sent to current time
   - Change status to "Declined Email Sent"
5. **Track** in state database to prevent duplicates

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Script not running | Check: `launchctl list \| grep com.meraglim.script_04` |
| Gmail auth error | Delete token: `rm ~/Automations/config/oauth_token.json` |
| No emails sent | Check logs: `tail -50 ~/Automations/logs/script_04_*.log` |
| Duplicate emails | Clear state: `rm ~/Automations/config/state.db` |
| Email formatting wrong | Check template in script, use `<p>` tags not `<br>` |

## Testing

1. Create test prospect in Airtable
2. Set `DRY_RUN = True` in script
3. Run manually and verify logs
4. Set `DRY_RUN = False`
5. Run manually and verify email received
6. Verify Airtable record updated
7. Run again to verify no duplicates

## Important Notes

- **Safety First:** `MAX_EMAILS_PER_RUN = 1` is intentional
- **State Tracking:** Prevents duplicate emails to same prospect
- **OAuth:** First run may require browser authentication
- **Interval:** 15 minutes between executions (adjustable)

## Email Template

The script sends a professional decline email that includes:
- Personalized greeting with prospect's first name
- Explanation of why they're not a fit
- Mention of their company
- Professional signature

Template uses HTML with `<p>` tags for proper formatting in Gmail.

---

**Quick Help:** For full details, see `SCRIPT_04_README.md` and `SCRIPT_04_DEPLOYMENT_CHECKLIST.md`
