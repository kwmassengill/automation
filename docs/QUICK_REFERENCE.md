# Script 6: Quick Reference Guide

## Common Commands

### Run the Script

```bash
# Manual execution
python3 ~/Automations/scripts/script_06_qualified_prospect_clickup.py

# With dry run (test mode)
DRY_RUN=true python3 ~/Automations/scripts/script_06_qualified_prospect_clickup.py
```

### View Logs

```bash
# Today's log (real-time)
tail -f ~/Automations/logs/script_06_qualified_prospect_clickup_$(date +%Y%m%d).log

# Error log
tail -f ~/Automations/logs/script_06_qualified_prospect_clickup_error.log

# Last 50 lines of error log
tail -50 ~/Automations/logs/script_06_qualified_prospect_clickup_error.log

# Search for specific errors
grep "ERROR" ~/Automations/logs/script_06_qualified_prospect_clickup_error.log | tail -20

# View all logs from past 24 hours
find ~/Automations/logs -name "script_06*.log" -mtime -1
```

### LaunchAgent Management

```bash
# Load (start) the agent
launchctl load ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist

# Unload (stop) the agent
launchctl unload ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist

# Check if loaded
launchctl list | grep com.meraglim.script06

# View agent status
launchctl list com.meraglim.script06_qualified_prospect_clickup

# Force run immediately
launchctl start com.meraglim.script06_qualified_prospect_clickup
```

### Configuration

```bash
# Edit environment variables
nano ~/Automations/config/.env

# View current configuration
cat ~/Automations/config/.env

# Test API connectivity
python3 << 'EOF'
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(os.path.expanduser("~/Automations/config/.env")))
print(f"AIRTABLE_BASE_ID: {os.getenv('AIRTABLE_BASE_ID')}")
print(f"CLICKUP_TEAM_ID: {os.getenv('CLICKUP_TEAM_ID')}")
EOF
```

### State Management

```bash
# View state database
sqlite3 ~/Automations/config/state.db "SELECT * FROM script_06_state;"

# Check processed records
sqlite3 ~/Automations/config/state.db "SELECT state_key, status, updated_at FROM script_06_state ORDER BY updated_at DESC LIMIT 10;"

# Clear state database (WARNING: will reprocess all records)
rm ~/Automations/config/state.db

# Backup state database
cp ~/Automations/config/state.db ~/Automations/config/state.db.backup.$(date +%Y%m%d_%H%M%S)
```

### File Management

```bash
# View script directory structure
tree ~/Automations/ -L 2

# Check disk usage
du -sh ~/Automations/*

# List recent log files
ls -lh ~/Automations/logs/ | tail -10

# Archive old logs
tar -czf ~/Automations/logs/archive_$(date +%Y%m%d).tar.gz ~/Automations/logs/*.log
```

---

## Troubleshooting Checklist

### Script Won't Run

- [ ] Check if Python 3 is installed: `python3 --version`
- [ ] Check if required packages installed: `pip3 list | grep requests`
- [ ] Check if script file exists: `ls -la ~/Automations/scripts/script_06*.py`
- [ ] Check file permissions: `chmod +x ~/Automations/scripts/script_06*.py`
- [ ] Check if `.env` file exists: `ls -la ~/Automations/config/.env`

### No ClickUp Tasks Created

- [ ] Check Airtable for matching prospects: `grep "Graduated to Deal Phase" ~/Automations/logs/*.log`
- [ ] Verify filter conditions in logs
- [ ] Check if "In Automation" field is populated
- [ ] Test API credentials manually
- [ ] Check ClickUp list ID is correct

### API Errors

- [ ] Check API credentials in `.env` file
- [ ] Verify API keys haven't expired
- [ ] Check network connectivity: `ping api.airtable.com`
- [ ] Check rate limits in logs
- [ ] Review API documentation for error codes

### LaunchAgent Issues

- [ ] Verify plist file exists: `ls -la ~/Library/LaunchAgents/com.meraglim.script06*.plist`
- [ ] Check plist syntax: `plutil -lint ~/Library/LaunchAgents/com.meraglim.script06*.plist`
- [ ] Check LaunchAgent logs: `log stream --predicate 'process == "script_06"' --level debug`
- [ ] Verify script path in plist matches actual location

---

## Performance Optimization

### Increase Processing Speed

```bash
# Edit script and increase MAX_RECORDS_PER_RUN
# Change: MAX_RECORDS_PER_RUN = 1
# To: MAX_RECORDS_PER_RUN = 10
nano ~/Automations/scripts/script_06_qualified_prospect_clickup.py
```

### Reduce LaunchAgent Frequency

```bash
# Edit plist and change StartInterval
# Current: 900 seconds (15 minutes)
# To run every 30 minutes: 1800
nano ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist

# Reload the agent
launchctl unload ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
launchctl load ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
```

---

## Debugging

### Enable Debug Logging

```bash
# Run with debug output
python3 -u ~/Automations/scripts/script_06_qualified_prospect_clickup.py 2>&1 | tee ~/Automations/logs/debug_$(date +%Y%m%d_%H%M%S).log
```

### Test Airtable Connection

```bash
python3 << 'EOF'
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(os.path.expanduser("~/Automations/config/.env")))

api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("AIRTABLE_BASE_ID")

url = f"https://api.airtable.com/v0/{base_id}/Prospects?maxRecords=1"
headers = {"Authorization": f"Bearer {api_key}"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(f"✓ Airtable connection successful")
    print(f"  Status: {response.status_code}")
    print(f"  Records: {len(response.json().get('records', []))}")
except Exception as e:
    print(f"✗ Airtable connection failed: {str(e)}")
EOF
```

### Test ClickUp Connection

```bash
python3 << 'EOF'
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(os.path.expanduser("~/Automations/config/.env")))

api_key = os.getenv("CLICKUP_API_KEY")
team_id = os.getenv("CLICKUP_TEAM_ID")

url = f"https://api.clickup.com/api/v2/team/{team_id}"
headers = {"Authorization": api_key}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(f"✓ ClickUp connection successful")
    print(f"  Status: {response.status_code}")
    print(f"  Team: {response.json().get('team', {}).get('name')}")
except Exception as e:
    print(f"✗ ClickUp connection failed: {str(e)}")
EOF
```

---

## Common Issues & Solutions

### "ModuleNotFoundError: No module named 'requests'"

```bash
# Install missing package
pip3 install requests

# Or use system pip
sudo pip3 install requests
```

### "FileNotFoundError: [Errno 2] No such file or directory: '/Users/.../Automations/config/.env'"

```bash
# Create missing .env file
cp ~/Automations/config/.env.template ~/Automations/config/.env

# Edit with your credentials
nano ~/Automations/config/.env
```

### "sqlite3.OperationalError: database is locked"

```bash
# Wait a moment and try again
# Or restart the script
launchctl stop com.meraglim.script06_qualified_prospect_clickup
sleep 5
launchctl start com.meraglim.script06_qualified_prospect_clickup
```

### "401 Unauthorized" from Airtable/ClickUp

```bash
# Verify API credentials
cat ~/Automations/config/.env | grep API_KEY

# Test with curl
curl -H "Authorization: Bearer YOUR_KEY" https://api.airtable.com/v0/meta/bases
```

---

## Useful Links

- **Airtable API:** https://airtable.com/api
- **ClickUp API:** https://clickup.com/api
- **Python Requests:** https://requests.readthedocs.io/
- **SQLite Documentation:** https://www.sqlite.org/cli.html
- **LaunchAgent Guide:** https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchAgents.html

---

## Quick Diagnostics

```bash
# Complete system check
echo "=== Script 6 Diagnostics ===" && \
echo "Python version:" && python3 --version && \
echo "Script exists:" && ls -la ~/Automations/scripts/script_06*.py && \
echo "Config exists:" && ls -la ~/Automations/config/.env && \
echo "Recent logs:" && ls -lh ~/Automations/logs/ | tail -5 && \
echo "LaunchAgent loaded:" && launchctl list | grep com.meraglim.script06 && \
echo "State database:" && ls -lh ~/Automations/config/state.db
```

---

## Emergency Procedures

### Stop All Executions

```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
```

### Restore from Backup

```bash
# Restore state database
cp ~/Automations/config/state.db.backup ~/Automations/config/state.db
```

### Reset Everything

```bash
# WARNING: This will reset all state tracking
rm ~/Automations/config/state.db
rm ~/Automations/logs/script_06*.log

# Restart the agent
launchctl unload ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
launchctl load ~/Library/LaunchAgents/com.meraglim.script06_qualified_prospect_clickup.plist
```
