# Script 6: Qualified Prospect → ClickUp Deal Pipeline

**Version:** 1.0.0  
**Date:** March 24, 2026  
**Status:** Production Ready  
**Complexity:** High (ClickUp API integration)

---

## Overview

Script 6 automatically creates ClickUp deal pipeline tasks when prospects reach "Graduated to Deal Phase" status in Airtable. This automation bridges your prospect qualification system with your deal pipeline management, ensuring no qualified prospects fall through the cracks.

### Key Features

- **Event-Driven Trigger:** Responds immediately to Airtable changes
- **Automatic Task Creation:** Creates ClickUp tasks with pre-filled prospect information
- **Custom Field Mapping:** Maps Airtable prospect data to ClickUp custom fields
- **Duplicate Prevention:** Uses SQLite state tracking to prevent duplicate ClickUp tasks
- **Comprehensive Logging:** Detailed logs for debugging and monitoring
- **Error Handling:** Exponential backoff retry logic for API failures
- **Email Notifications:** Sends alerts on critical errors
- **Dry Run Mode:** Test without creating actual ClickUp tasks

---

## Architecture

### Data Flow

```
Airtable (Prospects Table)
    ↓
    [Qualification Status = "Graduated to Deal Phase"]
    ↓
Script 6 (Python)
    ↓
    [Extract prospect data]
    ↓
    [Create ClickUp task]
    ↓
    [Track state in SQLite]
    ↓
ClickUp (Deal Pipeline List)
```

### Components

| Component | Purpose |
|-----------|---------|
| `script_06_qualified_prospect_clickup.py` | Main Python script with all logic |
| `.env` | Configuration file with API credentials |
| `state.db` | SQLite database for tracking processed records |
| `com.meraglim.script06_qualified_prospect_clickup.plist` | LaunchAgent configuration for Mac |
| Logs | Detailed execution logs for monitoring |

---

## Installation & Setup

### Prerequisites

- Python 3.7+
- Mac with LaunchAgent support (or Linux with cron)
- Airtable account with API access
- ClickUp account with API access
- Required Python packages: `requests`, `python-dotenv`

### Step 1: Create Directory Structure

```bash
mkdir -p ~/Automations/{scripts,config,logs,docs}
```

### Step 2: Copy Files

```bash
# Copy the main script
cp script_06_qualified_prospect_clickup.py ~/Automations/scripts/

# Copy the configuration template
cp .env.template ~/Automations/config/.env

# Copy the LaunchAgent plist
cp com.meraglim.script06_qualified_prospect_clickup.plist ~/Library/LaunchAgents/

# Copy documentation
cp README.md ~/Automations/docs/SCRIPT_06_README.md
cp QUICK_REFERENCE.md ~/Automations/docs/SCRIPT_06_QUICK_REFERENCE.md
cp DEPLOYMENT_CHECKLIST.md ~/Automations/docs/SCRIPT_06_DEPLOYMENT_CHECKLIST.md
cp LESSONS_LEARNED.md ~/Automations/docs/SCRIPT_06_LESSONS_LEARNED.md
```

### Step 3: Configure Environment Variables

Edit `~/Automations/config/.env` and add your credentials:

```env
AIRTABLE_API_KEY=your_api_key_here
AIRTABLE_BASE_ID=appoNkgoKHAUXgXV9
CLICKUP_API_KEY=your_clickup_api_key_here
CLICKUP_TEAM_ID=9017878084
CLICKUP_LIST_ID=901710776017
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com
```

### Step 4: Install Python Dependencies

```bash
pip3 install requests python-dotenv
```

### Step 5: Test with Dry Run

```bash
# Edit the script and set DRY_RUN = True
nano ~/Automations/scripts/script_06_qualified_prospect_clickup.py

# Run the script
python3 ~/Automations/scripts/script_06_qualified_prospect_clickup.py

# Check the logs
tail -f ~/Automations/logs/script_06_qualified_prospect_clickup_*.log
```

### Step 6: Deploy to Production

Once testing is successful:

1. Edit script and set `DRY_RUN = False`
2. Load the LaunchAgent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
   ```
3. Verify it's running:
   ```bash
   launchctl list | grep com.meraglim.script06
   ```

---

## Configuration Details

### Airtable Configuration

**Base ID:** `appoNkgoKHAUXgXV9` (Prospect Management System)  
**Table ID:** `tblxEhVek8ldTQMW1` (Prospects)

**Filter Conditions:**
- `Qualification Status` = "Graduated to Deal Phase"
- `In Automation` field exists

**Fields Used:**
- Company
- First Name
- Last Name
- Email
- Title
- Lead Source
- Qualification Score
- AI Analysis Notes

### ClickUp Configuration

**Team ID:** `9017878084` (Meraglim Holdings Corporation)  
**List ID:** `901710776017` (Qualified - Pre-Meeting)  
**Folder ID:** `90176860962` (Deal Pipeline)  
**Space ID:** `90174046780` (Corporate Development)

**Custom Fields Mapped:**
| ClickUp Field ID | Field Name | Source |
|---|---|---|
| 04337311-ead6-45a8-9b7e-cb1446e277ae | Company | Airtable Company |
| b357b002-bcb7-41d1-8d3f-8421ea63a719 | Email | Airtable Email |
| fd825748-8018-4100-91a2-273dbf58087d | Contact Name | Airtable First Name + Last Name |
| 1a4828a2-c794-4b63-92b6-18501e389d2f | Airtable Record | Airtable Record URL |

**Task Configuration:**
- Priority: High
- Due Date: 3 days from creation
- Assignee: Kevin Massengill (ID: 192268657)

---

## Usage

### Manual Execution

```bash
# Run the script manually
python3 ~/Automations/scripts/script_06_qualified_prospect_clickup.py

# Run with specific settings
DRY_RUN=true python3 ~/Automations/scripts/script_06_qualified_prospect_clickup.py
```

### Viewing Logs

```bash
# View today's log
tail -f ~/Automations/logs/script_06_qualified_prospect_clickup_$(date +%Y%m%d).log

# View error log
tail -f ~/Automations/logs/script_06_qualified_prospect_clickup_error.log

# Search for specific errors
grep "ERROR" ~/Automations/logs/script_06_qualified_prospect_clickup_error.log
```

### LaunchAgent Management

```bash
# Load the agent
launchctl load ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist

# Unload the agent
launchctl unload ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist

# Check if loaded
launchctl list | grep com.meraglim.script06

# View LaunchAgent logs
log stream --predicate 'process == "script_06_qualified_prospect_clickup"' --level debug
```

---

## Troubleshooting

### Issue: Script runs but creates no ClickUp tasks

**Possible Causes:**
1. No prospects with "Graduated to Deal Phase" status
2. "In Automation" field is empty for matching prospects
3. Airtable API key is invalid

**Solution:**
1. Check Airtable for matching records
2. Verify filter conditions in script
3. Validate API credentials in `.env`

### Issue: "API call failed" errors

**Possible Causes:**
1. API rate limiting (Airtable: 5 req/sec, ClickUp: 100 req/min)
2. Network connectivity issues
3. Invalid API credentials

**Solution:**
1. Script implements exponential backoff automatically
2. Check network connectivity
3. Verify API keys are correct and have necessary permissions

### Issue: Duplicate ClickUp tasks created

**Possible Causes:**
1. State database corrupted
2. Script ran multiple times simultaneously

**Solution:**
1. Delete state.db and restart (will reprocess records)
2. Ensure LaunchAgent interval is sufficient (default: 15 minutes)

### Issue: Email notifications not sending

**Possible Causes:**
1. Email credentials not configured
2. Gmail app password incorrect
3. SMTP connection issues

**Solution:**
1. Configure EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO in `.env`
2. Use Gmail App Password (not regular password)
3. Check firewall/network settings

---

## Performance & Limits

| Metric | Value | Notes |
|--------|-------|-------|
| Max Records Per Run | 1 (configurable) | Prevents mass operations |
| Airtable Rate Limit | 5 req/sec | Built-in retry logic handles this |
| ClickUp Rate Limit | 100 req/min | Built-in retry logic handles this |
| Retry Attempts | 3 | Exponential backoff: 1s, 2s, 4s |
| LaunchAgent Interval | 15 minutes | Configurable in plist |

---

## State Management

Script 6 uses SQLite to track processed records and prevent duplicates.

**State Database Location:** `~/Automations/config/state.db`

**State Table Schema:**
```sql
CREATE TABLE script_06_state (
    state_key TEXT PRIMARY KEY,
    last_processed_id TEXT,
    last_processed_timestamp TEXT,
    clickup_task_id TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT
)
```

**State Key Format:** `script_06_{airtable_record_id}_to_clickup`

---

## Monitoring & Alerts

### Log Levels

| Level | Purpose | Example |
|-------|---------|---------|
| DEBUG | Detailed execution flow | "Extracted prospect data: Company - Name" |
| INFO | Important events | "Successfully created ClickUp task 123" |
| WARNING | Potential issues | "API call failed, retrying in 2s" |
| ERROR | Failures | "Failed to create ClickUp task: 400 Bad Request" |

### Email Alerts

Script sends email notifications for:
- Critical script errors
- API failures after all retries
- Configuration issues

Configure email in `.env` file.

---

## Best Practices

1. **Always test with DRY_RUN = True first** before production deployment
2. **Monitor logs regularly** for errors and performance issues
3. **Keep credentials secure** - never commit `.env` to version control
4. **Verify field mappings** when Airtable or ClickUp schema changes
5. **Check state database** periodically for orphaned records
6. **Update documentation** when making configuration changes

---

## Maintenance

### Regular Tasks

- **Weekly:** Review error logs for patterns
- **Monthly:** Verify API credentials are still valid
- **Quarterly:** Update documentation with any changes

### Backup

```bash
# Backup state database
cp ~/Automations/config/state.db ~/Automations/config/state.db.backup

# Backup logs
tar -czf ~/Automations/logs/logs_backup_$(date +%Y%m%d).tar.gz ~/Automations/logs/
```

---

## Support & Documentation

- **Quick Reference:** See `QUICK_REFERENCE.md`
- **Deployment Checklist:** See `DEPLOYMENT_CHECKLIST.md`
- **Lessons Learned:** See `LESSONS_LEARNED.md`
- **API Documentation:** 
  - Airtable: https://airtable.com/api
  - ClickUp: https://clickup.com/api

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-24 | Initial release |

---

## License

Internal use only. Part of Meraglim Holdings Corporation automation suite.
