# Script 6: Deployment Checklist

**Date:** March 24, 2026  
**Script:** Qualified Prospect → ClickUp Deal Pipeline  
**Deployed By:** _______________  
**Deployment Date:** _______________

---

## Pre-Deployment Phase

### 1. File Preparation

- [ ] Extract all Script 6 files from Dropbox
- [ ] Verify all files are present:
  - [ ] `script_06_qualified_prospect_clickup.py`
  - [ ] `.env.template`
  - [ ] `com.meraglim.script06_qualified_prospect_clickup.plist`
  - [ ] `README.md`
  - [ ] `QUICK_REFERENCE.md`
  - [ ] `DEPLOYMENT_CHECKLIST.md`
  - [ ] `LESSONS_LEARNED.md`
- [ ] Check file integrity (no corruption)
- [ ] Verify file permissions are readable

### 2. Environment Setup

- [ ] Create directory structure:
  ```bash
  mkdir -p ~/Automations/{scripts,config,logs,docs}
  ```
- [ ] Verify directories created successfully
- [ ] Check directory permissions (should be user-readable)

### 3. Credential Verification

- [ ] Obtain Airtable API key from https://airtable.com/account/tokens
- [ ] Obtain ClickUp API key from https://app.clickup.com/settings/integrations/api
- [ ] Verify Airtable Base ID: `appoNkgoKHAUXgXV9`
- [ ] Verify ClickUp Team ID: `9017878084`
- [ ] Verify ClickUp List ID: `901710776017`
- [ ] Test Airtable credentials manually
- [ ] Test ClickUp credentials manually

### 4. Python Environment

- [ ] Verify Python 3.7+ installed: `python3 --version`
- [ ] Install required packages:
  ```bash
  pip3 install requests python-dotenv
  ```
- [ ] Verify packages installed: `pip3 list | grep -E "requests|python-dotenv"`

---

## Installation Phase

### 5. Copy Files to Mac

- [ ] Copy main script:
  ```bash
  cp script_06_qualified_prospect_clickup.py ~/Automations/scripts/
  ```
- [ ] Verify script copied: `ls -la ~/Automations/scripts/script_06*.py`

- [ ] Copy configuration template:
  ```bash
  cp .env.template ~/Automations/config/.env.template
  cp .env.template ~/Automations/config/.env
  ```
- [ ] Verify config files copied: `ls -la ~/Automations/config/.env*`

- [ ] Copy LaunchAgent plist:
  ```bash
  cp com.meraglim.script06_qualified_prospect_clickup.plist ~/Library/LaunchAgents/
  ```
- [ ] Verify plist copied: `ls -la ~/Library/LaunchAgents/com.meraglim.script06*.plist`

- [ ] Copy documentation:
  ```bash
  cp README.md ~/Automations/docs/SCRIPT_06_README.md
  cp QUICK_REFERENCE.md ~/Automations/docs/SCRIPT_06_QUICK_REFERENCE.md
  cp DEPLOYMENT_CHECKLIST.md ~/Automations/docs/SCRIPT_06_DEPLOYMENT_CHECKLIST.md
  cp LESSONS_LEARNED.md ~/Automations/docs/SCRIPT_06_LESSONS_LEARNED.md
  ```
- [ ] Verify docs copied: `ls -la ~/Automations/docs/SCRIPT_06*.md`

### 6. Configure Environment Variables

- [ ] Edit `.env` file:
  ```bash
  nano ~/Automations/config/.env
  ```
- [ ] Add Airtable credentials:
  - [ ] AIRTABLE_API_KEY
  - [ ] AIRTABLE_BASE_ID
- [ ] Add ClickUp credentials:
  - [ ] CLICKUP_API_KEY
  - [ ] CLICKUP_TEAM_ID
  - [ ] CLICKUP_LIST_ID
- [ ] Add email configuration (optional):
  - [ ] SMTP_SERVER
  - [ ] SMTP_PORT
  - [ ] EMAIL_FROM
  - [ ] EMAIL_PASSWORD
  - [ ] EMAIL_TO
- [ ] Verify `.env` file saved: `cat ~/Automations/config/.env | grep -v "^#" | grep -v "^$"`

### 7. Verify File Permissions

- [ ] Make script executable:
  ```bash
  chmod +x ~/Automations/scripts/script_06_qualified_prospect_clickup.py
  ```
- [ ] Verify permissions: `ls -la ~/Automations/scripts/script_06*.py`

- [ ] Verify plist is readable:
  ```bash
  chmod 644 ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
  ```

---

## Testing Phase

### 8. Dry Run Testing

- [ ] Edit script and verify `DRY_RUN = True`:
  ```bash
  grep "DRY_RUN = " ~/Automations/scripts/script_06_qualified_prospect_clickup.py
  ```

- [ ] Create test prospect in Airtable:
  - [ ] Company: "Test Company"
  - [ ] First Name: "Test"
  - [ ] Last Name: "Prospect"
  - [ ] Email: "test@example.com"
  - [ ] Qualification Status: "Graduated to Deal Phase"
  - [ ] In Automation: "Yes" (or any value)

- [ ] Run script in dry run mode:
  ```bash
  python3 ~/Automations/scripts/script_06_qualified_prospect_clickup.py
  ```

- [ ] Check logs for expected output:
  ```bash
  tail -50 ~/Automations/logs/script_06_qualified_prospect_clickup_$(date +%Y%m%d).log
  ```

- [ ] Verify log contains:
  - [ ] "Found 1 qualified prospects to process"
  - [ ] "[DRY RUN] Would create ClickUp task"
  - [ ] "Processing Summary"

- [ ] Verify NO ClickUp tasks were actually created

### 9. API Connectivity Testing

- [ ] Test Airtable connection:
  ```bash
  python3 << 'EOF'
  import os, requests
  from dotenv import load_dotenv
  from pathlib import Path
  load_dotenv(Path(os.path.expanduser("~/Automations/config/.env")))
  api_key = os.getenv("AIRTABLE_API_KEY")
  base_id = os.getenv("AIRTABLE_BASE_ID")
  url = f"https://api.airtable.com/v0/{base_id}/Prospects?maxRecords=1"
  headers = {"Authorization": f"Bearer {api_key}"}
  response = requests.get(url, headers=headers)
  print(f"Status: {response.status_code}")
  print(f"Success: {response.status_code == 200}")
  EOF
  ```
- [ ] Verify Airtable connection successful

- [ ] Test ClickUp connection:
  ```bash
  python3 << 'EOF'
  import os, requests
  from dotenv import load_dotenv
  from pathlib import Path
  load_dotenv(Path(os.path.expanduser("~/Automations/config/.env")))
  api_key = os.getenv("CLICKUP_API_KEY")
  team_id = os.getenv("CLICKUP_TEAM_ID")
  url = f"https://api.clickup.com/api/v2/team/{team_id}"
  headers = {"Authorization": api_key}
  response = requests.get(url, headers=headers)
  print(f"Status: {response.status_code}")
  print(f"Success: {response.status_code == 200}")
  EOF
  ```
- [ ] Verify ClickUp connection successful

### 10. State Database Testing

- [ ] Verify state database created:
  ```bash
  ls -la ~/Automations/config/state.db
  ```

- [ ] Test state database:
  ```bash
  sqlite3 ~/Automations/config/state.db "SELECT COUNT(*) FROM script_06_state;"
  ```

- [ ] Verify database is readable and writable

---

## Production Deployment Phase

### 11. Enable Production Mode

- [ ] Edit script and set `DRY_RUN = False`:
  ```bash
  nano ~/Automations/scripts/script_06_qualified_prospect_clickup.py
  # Change: DRY_RUN = True
  # To: DRY_RUN = False
  ```

- [ ] Verify change saved:
  ```bash
  grep "DRY_RUN = " ~/Automations/scripts/script_06_qualified_prospect_clickup.py
  ```

### 12. Load LaunchAgent

- [ ] Verify plist syntax:
  ```bash
  plutil -lint ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
  ```
- [ ] Output should show: "OK"

- [ ] Load the LaunchAgent:
  ```bash
  launchctl load ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
  ```

- [ ] Verify LaunchAgent loaded:
  ```bash
  launchctl list | grep com.meraglim.script06
  ```
- [ ] Should show the agent with PID

### 13. Production Testing

- [ ] Create test prospect in Airtable with:
  - [ ] Qualification Status: "Graduated to Deal Phase"
  - [ ] In Automation: "Yes"

- [ ] Wait for LaunchAgent to run (max 15 minutes)

- [ ] Check logs:
  ```bash
  tail -50 ~/Automations/logs/script_06_qualified_prospect_clickup_$(date +%Y%m%d).log
  ```

- [ ] Verify ClickUp task was created:
  - [ ] Log in to ClickUp
  - [ ] Navigate to "Qualified - Pre-Meeting" list
  - [ ] Verify test prospect task exists
  - [ ] Verify custom fields are populated

- [ ] Verify state database was updated:
  ```bash
  sqlite3 ~/Automations/config/state.db "SELECT * FROM script_06_state ORDER BY updated_at DESC LIMIT 1;"
  ```

### 14. Monitoring Setup

- [ ] Set up log monitoring:
  ```bash
  tail -f ~/Automations/logs/script_06_qualified_prospect_clickup_$(date +%Y%m%d).log
  ```

- [ ] Configure email alerts (if applicable):
  - [ ] Verify EMAIL_FROM is set in `.env`
  - [ ] Verify EMAIL_PASSWORD is set in `.env`
  - [ ] Verify EMAIL_TO is set in `.env`
  - [ ] Send test email to verify configuration

- [ ] Create calendar reminder to check logs weekly

---

## Post-Deployment Phase

### 15. Documentation & Handoff

- [ ] Update deployment notes:
  - [ ] Deployment date: _______________
  - [ ] Deployed by: _______________
  - [ ] Any issues encountered: _______________

- [ ] Create backup of configuration:
  ```bash
  cp ~/Automations/config/.env ~/Automations/config/.env.backup.$(date +%Y%m%d)
  cp ~/Automations/config/state.db ~/Automations/config/state.db.backup.$(date +%Y%m%d)
  ```

- [ ] Archive initial logs:
  ```bash
  tar -czf ~/Automations/logs/initial_deployment_$(date +%Y%m%d).tar.gz ~/Automations/logs/script_06*.log
  ```

- [ ] Share documentation with team:
  - [ ] README.md
  - [ ] QUICK_REFERENCE.md
  - [ ] LESSONS_LEARNED.md

### 16. Monitoring & Maintenance

- [ ] Schedule weekly log reviews
- [ ] Monitor for errors in error log
- [ ] Track processing statistics:
  - [ ] Records processed per week
  - [ ] Success rate
  - [ ] Average processing time

- [ ] Set up quarterly maintenance:
  - [ ] Verify API credentials still valid
  - [ ] Check for schema changes in Airtable/ClickUp
  - [ ] Review and update documentation

---

## Rollback Procedures

If issues occur after deployment:

### Immediate Rollback

```bash
# Stop the LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist

# Restore from backup
cp ~/Automations/config/.env.backup ~/Automations/config/.env
cp ~/Automations/config/state.db.backup ~/Automations/config/state.db

# Restore previous script version if needed
# (Keep backup of previous working version)
```

### Partial Rollback

```bash
# Set DRY_RUN = True to investigate issues
nano ~/Automations/scripts/script_06_qualified_prospect_clickup.py

# Run in test mode
python3 ~/Automations/scripts/script_06_qualified_prospect_clickup.py

# Review logs
tail -100 ~/Automations/logs/script_06_qualified_prospect_clickup_error.log
```

---

## Sign-Off

- [ ] All checklist items completed
- [ ] Script is running in production
- [ ] Logs are being generated
- [ ] No critical errors in error log
- [ ] Team notified of deployment

**Deployment Completed By:** _______________  
**Date:** _______________  
**Time:** _______________  
**Notes:** _______________________________________________________________

---

## Emergency Contacts

- **Primary Contact:** _______________
- **Backup Contact:** _______________
- **Escalation Contact:** _______________

---

## Lessons Learned

Document any issues or improvements discovered during deployment:

1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

---

## Next Steps

- [ ] Monitor for 24 hours after deployment
- [ ] Review logs daily for first week
- [ ] Schedule follow-up meeting after 1 week
- [ ] Plan for Scripts 7-12 migration
