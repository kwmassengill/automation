# Script 8: Meeting Scheduled → ClickUp Prep Task

**Status:** Production Ready  
**Version:** 1.0.0  
**Last Updated:** March 24, 2026  
**Replaces:** Make.com Scenario 8

---

## Executive Summary

Script 8 automates the creation of meeting preparation tasks in ClickUp whenever a prospect's status in Airtable changes to "Meeting Scheduled". This script runs every 15 minutes on your Mac via LaunchAgent, ensuring that no scheduled meetings are missed.

The implementation is based on the Make.com blueprint but includes enhancements for reliability, logging, and error handling. All four filter conditions from the original blueprint are explicitly implemented in Python to ensure exact behavior replication.

---

## What This Script Does

1. **Monitors Airtable** for records with `Qualification Status = "Meeting Scheduled"`
2. **Applies strict filtering** to ensure all required data is present (Email, Meeting Date, In Automation flag)
3. **Creates a ClickUp task** with:
   - Task name: `[Company] Discover Call - [Prospect Name]`
   - Rich Markdown description with prospect details and pre-call checklist
   - Custom fields: EBITDA Range, Payment Preference, Airtable Record Link, etc.
   - Due date set to the meeting date
4. **Updates Airtable** with the ClickUp Task ID and changes status to "Prep Task Created"
5. **Prevents duplicates** through state tracking and Airtable status updates

---

## The Four Filter Conditions

The Make.com blueprint includes four filter conditions that must ALL be true for a record to be processed. These are explicitly implemented in the Python script:

| Condition | Field | Operator | Value | Purpose |
|-----------|-------|----------|-------|---------|
| 1 | Qualification Status | Text: Equal to | "Meeting Scheduled" | Primary trigger |
| 2 | Email | Basic: Exists | (any value) | Ensure contact info |
| 3 | Meeting Date | Basic: Exists | (any value) | Ensure meeting scheduled |
| 4 | In Automation | Basic: Exists | (checked) | Automation flag |

All conditions use AND logic. If any single condition fails, the record is skipped.

---

## File Structure

```
/Users/kevinmassengill/Automations/
├── scripts/
│   ├── script_08_meeting_scheduled_clickup.py    # Main script
│   └── shared_utils.py                            # Shared utilities
├── config/
│   ├── .env                                        # Credentials (not in git)
│   └── state.db                                    # SQLite state database
├── logs/
│   ├── script_08_meeting_scheduled_clickup_*.log  # Daily logs
│   └── script_08_stdout.log                        # LaunchAgent stdout
└── docs/
    ├── README_SCRIPT_8.md                          # This file
    ├── SCRIPT_8_DEPLOYMENT_GUIDE.md                # Deployment instructions
    └── SCRIPT_8_FILTER_ANALYSIS.md                 # Filter logic documentation

~/Library/LaunchAgents/
└── com.meraglim.script_08_meeting_scheduled_clickup.plist  # Scheduler
```

---

## Installation & Deployment

### Quick Start (5 minutes)

1. **Copy the script:**
   ```bash
   cp script_08_meeting_scheduled_clickup.py ~/Automations/scripts/
   chmod +x ~/Automations/scripts/script_08_meeting_scheduled_clickup.py
   ```

2. **Test in dry run mode:**
   ```bash
   # Ensure DRY_RUN=True in .env
   python3 ~/Automations/scripts/script_08_meeting_scheduled_clickup.py
   ```

3. **Enable production mode:**
   ```bash
   # Change DRY_RUN=False in .env
   # Test once more with real data
   python3 ~/Automations/scripts/script_08_meeting_scheduled_clickup.py
   ```

4. **Schedule with LaunchAgent:**
   ```bash
   cp com.meraglim.script_08_meeting_scheduled_clickup.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.meraglim.script_08_meeting_scheduled_clickup.plist
   ```

5. **Verify it's running:**
   ```bash
   launchctl list | grep script_08
   # Should show: 0 com.meraglim.script_08_meeting_scheduled_clickup
   ```

---

## Configuration

### Required Environment Variables

Edit `/Users/kevinmassengill/Automations/config/.env`:

```bash
# Airtable Configuration
AIRTABLE_API_KEY=pat_xxxxxxxxxxxxx
AIRTABLE_BASE_ID=appoNkgoKHAUXgXV9
AIRTABLE_TABLE_ID=tblxEhVek8ldTQMW1

# ClickUp Configuration
CLICKUP_API_KEY=pk_xxxxxxxxxxxxx
CLICKUP_TEAM_ID=90174046780
CLICKUP_LIST_ID=901711223397

# Script Configuration
DRY_RUN=False                    # Set to True for testing
MAX_TASKS_PER_RUN=10             # Max tasks per execution
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
```

### Optional Configuration

```bash
# Paths (defaults shown)
AUTOMATION_BASE_PATH=/Users/kevinmassengill/Automations
LOG_DIR=/Users/kevinmassengill/Automations/logs
STATE_DB_PATH=/Users/kevinmassengill/Automations/config/state.db

# Email notifications (optional)
NOTIFICATION_EMAIL=your@email.com
NOTIFICATION_EMAIL_PASSWORD=your_app_password
```

---

## Monitoring & Logs

### View Real-Time Logs

```bash
# View last 50 lines
tail -50 ~/Automations/logs/script_08_meeting_scheduled_clickup_*.log

# Follow logs in real-time
tail -f ~/Automations/logs/script_08_meeting_scheduled_clickup_*.log
```

### Check LaunchAgent Status

```bash
# List all running agents
launchctl list | grep script_08

# View LaunchAgent output
cat ~/Automations/logs/script_08_stdout.log
cat ~/Automations/logs/script_08_stderr.log

# Check if agent ran recently
log stream --predicate 'process == "launchd"' | grep script_08
```

### Common Log Messages

- **`[DRY RUN] Would create ClickUp task`** - Script is in dry run mode, not actually creating tasks
- **`filtered out: No Email`** - Record missing email address
- **`filtered out: No Meeting Date`** - Record missing meeting date
- **`filtered out: 'In Automation' flag not set`** - Automation checkbox not checked
- **`Successfully created ClickUp task`** - Task created successfully
- **`Successfully updated Airtable record`** - Airtable record updated with task ID

---

## Troubleshooting

### Tasks Not Being Created

**Step 1: Check if records are found**
```bash
grep "Found.*records" ~/Automations/logs/script_08_*.log
```
If it shows 0 records, check that Airtable records have status "Meeting Scheduled".

**Step 2: Check filter logs**
```bash
grep "filtered out" ~/Automations/logs/script_08_*.log
```
This shows why records are being skipped. Common reasons:
- Missing email address
- Missing meeting date
- "In Automation" checkbox is unchecked

**Step 3: Check API errors**
```bash
grep "error\|Error\|ERROR" ~/Automations/logs/script_08_*.log
```

### LaunchAgent Not Running

**Check if loaded:**
```bash
launchctl list | grep script_08
# Should show: 0 com.meraglim.script_08_meeting_scheduled_clickup
```

**If not loaded:**
```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script_08_meeting_scheduled_clickup.plist
```

**Check plist syntax:**
```bash
plutil -lint ~/Library/LaunchAgents/com.meraglim.script_08_meeting_scheduled_clickup.plist
```

**Force manual run:**
```bash
launchctl start com.meraglim.script_08_meeting_scheduled_clickup
```

### API Authentication Errors

**401 Unauthorized from ClickUp:**
```bash
# Verify API key is correct
echo $CLICKUP_API_KEY
# Test with curl
curl -H "Authorization: pk_YOUR_KEY" https://api.clickup.com/api/v2/team
```

**401 Unauthorized from Airtable:**
```bash
# Verify API key is correct
echo $AIRTABLE_API_KEY
# Test with curl
curl -H "Authorization: Bearer YOUR_KEY" https://api.airtable.com/v0/meta/bases
```

---

## Performance & Limits

- **Execution Time:** Typically 2-5 seconds per run
- **Max Tasks Per Run:** 10 (configurable via `MAX_TASKS_PER_RUN`)
- **Run Frequency:** Every 15 minutes (900 seconds)
- **API Rate Limits:** Airtable (5 req/sec), ClickUp (100 req/min)

---

## Maintenance

### Weekly Checks

1. Verify LaunchAgent is still running:
   ```bash
   launchctl list | grep script_08
   ```

2. Check for errors in logs:
   ```bash
   grep ERROR ~/Automations/logs/script_08_*.log | tail -10
   ```

3. Verify ClickUp tasks are being created with correct data

### Monthly Maintenance

1. Archive old log files (older than 30 days)
2. Review state database for any orphaned records
3. Check ClickUp custom field IDs haven't changed

### Quarterly Reviews

1. Review Make.com blueprint for any changes
2. Update custom field mappings if needed
3. Test dry run mode to verify logic still works

---

## Differences from Make.com

| Aspect | Make.com | Python Script |
|--------|----------|---------------|
| Trigger | Airtable watch | Airtable API query every 15 min |
| Filter | Visual UI | Explicit Python function |
| Error Handling | Limited | Comprehensive logging + email |
| State Management | Make.com internal | SQLite database |
| Scheduling | Make.com | Mac LaunchAgent |
| Logging | Limited | Full audit trail |
| Testing | Limited | Dry run mode |

---

## Success Criteria

Script 8 is working correctly when:

✅ **Functionality**
- Detects meetings with status "Meeting Scheduled"
- Creates ClickUp task with correct name and description
- Updates Airtable with ClickUp Task ID
- Changes status to "Prep Task Created"
- Runs every 15 minutes without errors

✅ **Reliability**
- 100% of qualifying meetings get tasks created
- Zero duplicate tasks
- Zero failed Airtable updates
- Zero unhandled exceptions

✅ **Performance**
- Processes all pending meetings within 5 minutes
- No API rate limit errors
- No timeout errors

✅ **Maintainability**
- Code is well-documented
- All functions have docstrings
- Error messages are clear and actionable
- Logs are comprehensive and searchable

---

## Support & Escalation

If you encounter issues:

1. **Check logs first:** Most issues are visible in the logs
2. **Review this documentation:** Common issues are covered in Troubleshooting
3. **Test in dry run mode:** Verify the logic without making changes
4. **Check API credentials:** Ensure .env file has correct keys
5. **Review Make.com blueprint:** Compare Python logic to original blueprint

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-24 | Initial release from Make.com migration |

---

## License & Attribution

This script was created as part of the Local Automations – Make.com Migration project. It replicates the functionality of Make.com Scenario 8 with enhancements for reliability and maintainability.

**Created by:** Manus AI  
**For:** Kevin Massengill  
**Date:** March 24, 2026
