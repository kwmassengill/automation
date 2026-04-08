# Meraglim Holdings - Local Automations Master README

## Project Overview

This project converts 12 Make.com automation blueprints into persistent local Python scripts that run on macOS using LaunchAgents. All scripts execute locally with zero Manus involvement, preventing unexpected charges and ensuring reliability.

**Status:** 🟢 Active - Scripts 1 & 7 running, Scripts 2-6 & 8-11 in development

**Cost:** $0 - All automation runs locally on your Mac

## Quick Start

### Check All Scripts Status
```bash
launchctl list | grep com.meraglim
```

### View Real-time Logs
```bash
tail -f ~/Automations/logs/script_01.log
```

### Stop All Scripts
```bash
for plist in ~/Library/LaunchAgents/com.meraglim.*.plist; do
  launchctl unload "$plist"
done
```

### Start All Scripts
```bash
for plist in ~/Library/LaunchAgents/com.meraglim.*.plist; do
  launchctl load "$plist"
done
```

## ⚠️ NEW AGENT ONBOARDING

**If you are a new Manus agent starting a task in this project, STOP and read `NEW_TASK_ONBOARDING.md` and `SCRIPTS_REGISTRY.md` immediately.**

These two files are the single source of truth for the project architecture and the current status of all 20+ scripts. Do not rely on this README for script status, as it may be outdated.

## Project Structure

```
~/Automations/
├── README_MASTER.md                    # This file
├── LAUNCHAGENT_SETUP.md               # How to create/manage LaunchAgents
├── SCRIPT_DEPLOYMENT_TEMPLATE.md      # Template for deploying new scripts
├── TROUBLESHOOTING_AND_LESSONS.md     # Known issues & solutions
├── scripts/
│   ├── script_01_google_sheets_to_airtable.py       ✅ ACTIVE
│   ├── script_02_airtable_qualification_email.py    ⏳ Pending
│   ├── script_03_qualified_prospect_calendar_invite.py ⏳ Pending
│   ├── script_04_not_qualified_polite_decline.py    ⏳ Pending
│   ├── script_05_qualified_7day_followup.py         ⏳ Pending
│   ├── script_06_qualified_prospect_clickup_deal.py ⏳ Pending
│   ├── script_07_gmail_reply_ai_qualification.py    ✅ ACTIVE
│   ├── script_08_meeting_scheduled_clickup_prep.py  ⏳ Pending
│   ├── script_09_mhc10_meeting_intelligence_trigger.py ⏳ Pending
│   ├── script_10_mhc10_meeting_intelligence_summary.py ⏳ Pending
│   ├── script_11_mhc11_post_meeting_intelligence.py ⏳ Pending
│   └── shared_utils.py                 # Common utilities for all scripts
├── config/
│   ├── .env                           # API credentials (NEVER commit)
│   └── state.db                       # SQLite state tracking database
├── logs/
│   ├── script_01.log                  # Script 1 output logs
│   ├── script_01_error.log            # Script 1 error logs
│   ├── script_XX.log                  # Other script logs
│   └── cron.log                       # Cron execution history
└── blueprints/
    ├── blueprint_01.json              # Original Make.com blueprints
    ├── blueprint_02.json
    ├── ...
    └── blueprint_12.json
```

## Scripts Overview

### ✅ Active Scripts

#### Script 1: Google Sheets to Airtable Sync
- **Purpose:** Syncs new prospects from Google Sheets (Leads tab) to Airtable Prospects table
- **Trigger:** Every 5 minutes via LaunchAgent
- **Status:** ✅ ACTIVE & TESTED
- **Input:** Google Sheets (spreadsheet ID: 1NX2xxzkKUO-EY2QXO_OtHQTaqGV8dvbxXikGMBoeS-g)
- **Output:** Airtable Prospects table (Base: appoNkgoKHAUXgXV9, Table: tblxEhVek8ldTQMW1)
- **Key Features:**
  - Duplicate prevention by email
  - State tracking (prevents reprocessing)
  - Processes 10 rows per execution
  - Comprehensive error logging
- **LaunchAgent:** `com.meraglim.script01`
- **Logs:** `~/Automations/logs/script_01.log`

#### Script 7: Gmail Reply AI Qualification
- **Purpose:** Monitors for email replies, searches Airtable for prospect, uses AI to qualify
- **Trigger:** Every 5 minutes via LaunchAgent
- **Status:** ✅ ACTIVE & TESTED
- **Input:** Gmail (filters: subject contains "Re:", NOT from @meraglim.com)
- **Output:** Airtable Prospects table (updates qualification status)
- **Key Features:**
  - Gmail filter for replies only
  - Airtable search filter (only proceeds if prospect found)
  - OpenAI GPT-4.1-mini for AI qualification
  - Marks emails as read after processing
- **LaunchAgent:** `com.meraglim.script07`
- **Logs:** `~/Automations/logs/script_07.log`

### ⏳ Pending Scripts (To Be Created)

| Script | Purpose | Trigger | Status |
|--------|---------|---------|--------|
| Script 2 | Send qualification email to new prospect | New Airtable record | Pending |
| Script 3 | Create calendar invite for qualified prospect | Qualified status in Airtable | Pending |
| Script 4 | Send polite decline to not-qualified prospect | Not qualified status | Pending |
| Script 5 | Send 7-day follow-up email | 7 days after initial contact | Pending |
| Script 6 | Create ClickUp deal for qualified prospect | Qualified status | Pending |
| Script 8 | Prepare ClickUp task when meeting scheduled | Meeting scheduled in calendar | Pending |
| Script 9 | Trigger meeting intelligence on meeting start | Meeting starts | Pending |
| Script 10 | Generate meeting intelligence summary | Meeting ends | Pending |
| Script 11 | Post-meeting intelligence processing | After meeting | Pending |

## Configuration

### Environment Variables (.env)

Located at: `~/.env`

**Required variables:**
```
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=appoNkgoKHAUXgXV9
GOOGLE_TOKEN_FILE=/Users/kevinmassengill/Automations/config/google_token.json
OPENAI_API_KEY=your_openai_api_key
CLICKUP_API_KEY=your_clickup_api_key
CLAY_API_KEY=your_clay_api_key
```

**⚠️ IMPORTANT:** Never commit `.env` file to version control

### State Database

Located at: `~/Automations/config/state.db`

SQLite database tracking:
- Last processed row/record ID
- Last execution timestamp
- Error counts
- Script status

**Query state:**
```bash
sqlite3 ~/Automations/config/state.db "SELECT * FROM script_state;"
```

## APIs & Integrations

| API | Purpose | Credentials | Status |
|-----|---------|-------------|--------|
| Google Sheets | Read prospect data | GOOGLE_TOKEN_FILE | ✅ Active |
| Airtable | Store & update prospects | AIRTABLE_API_KEY | ✅ Active |
| Gmail | Monitor email replies | MCP Integration | ✅ Active |
| OpenAI | AI qualification | OPENAI_API_KEY | ✅ Active |
| ClickUp | Task/deal management | CLICKUP_API_KEY | ⏳ Pending |
| Clay | Data enrichment | CLAY_API_KEY | ⏳ Pending |

## Logging & Monitoring

### Log Files

All logs stored in: `~/Automations/logs/`

**Format:** `YYYY-MM-DD HH:MM:SS - script_name - LEVEL - message`

**Log Levels:**
- `INFO` - Normal operation
- `WARNING` - Potential issues
- `ERROR` - Errors caught and handled
- `CRITICAL` - Fatal errors requiring attention

### View Logs

**Real-time monitoring:**
```bash
tail -f ~/Automations/logs/script_01.log
```

**Last 50 lines:**
```bash
tail -50 ~/Automations/logs/script_01.log
```

**Search for errors:**
```bash
grep ERROR ~/Automations/logs/script_01.log
```

**View all logs:**
```bash
ls -lh ~/Automations/logs/
```

## LaunchAgent Management

### Check Status
```bash
launchctl list | grep com.meraglim
```

### Load a Script
```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.scriptXX.plist
```

### Unload a Script
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.scriptXX.plist
```

### Reload (Restart) a Script
```bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.scriptXX.plist
launchctl load ~/Library/LaunchAgents/com.meraglim.scriptXX.plist
```

### View Plist File
```bash
cat ~/Library/LaunchAgents/com.meraglim.scriptXX.plist
```

## Troubleshooting

### Script Not Running

1. **Check if LaunchAgent is loaded:**
   ```bash
   launchctl list | grep com.meraglim.scriptXX
   ```

2. **Check for errors:**
   ```bash
   tail -50 ~/Automations/logs/script_XX_error.log
   ```

3. **Reload the LaunchAgent:**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.meraglim.scriptXX.plist
   launchctl load ~/Library/LaunchAgents/com.meraglim.scriptXX.plist
   ```

### Unexpected Manus Tasks

**This should NOT happen anymore.** If you see new "Sync Prospects" tasks in Manus:

1. Check Manus "Scheduled" tasks
2. Delete any active schedules
3. Verify LaunchAgent is still loaded
4. Contact support

See: `TROUBLESHOOTING_AND_LESSONS.md`

### API Errors

**Check credentials:**
```bash
cat ~/.env | grep -E "AIRTABLE|GOOGLE|OPENAI"
```

**Test script manually:**
```bash
/usr/bin/python3 ~/Automations/scripts/script_XX_description.py
```

**Check API rate limits:**
- Airtable: 5 requests/second
- Google Sheets: 300 requests/minute
- OpenAI: Check your plan limits

## Important Files & References

| File | Purpose | Access |
|------|---------|--------|
| `LAUNCHAGENT_SETUP.md` | How to create/manage LaunchAgents | Read first |
| `SCRIPT_DEPLOYMENT_TEMPLATE.md` | Template for new scripts | Use for Scripts 2-12 |
| `TROUBLESHOOTING_AND_LESSONS.md` | Known issues & solutions | Reference when problems occur |
| `shared_utils.py` | Common utilities | Used by all scripts |
| `.env` | API credentials | NEVER commit |
| `state.db` | Script state tracking | SQLite database |

## Critical Lessons Learned

### ❌ What NOT to Do

1. **Never use Manus scheduler** for local script execution
2. **Never hardcode credentials** in scripts
3. **Never skip error handling** in scripts
4. **Never forget to test** scripts manually first
5. **Never ignore logs** when troubleshooting

### ✅ What TO Do

1. **Always use LaunchAgent** for macOS automation
2. **Always store credentials** in `.env` file
3. **Always include error handling** and logging
4. **Always test manually** before scheduling
5. **Always monitor logs** for first 24 hours

See: `TROUBLESHOOTING_AND_LESSONS.md` for full details

## Manus Integration

### How Manus Accesses This Project

1. **Files Location:** `/mnt/desktop/Make Blueprints/Automations/`
2. **Manus can read:** All markdown files and documentation
3. **Manus can reference:** Script locations and setup instructions
4. **Manus can update:** Documentation and checklists

### For Next Manus Session

When continuing this project:

1. **Read this README first** to understand the project
2. **Check status:** `launchctl list | grep com.meraglim`
3. **Review logs:** `tail -20 ~/Automations/logs/*.log`
4. **Check for issues:** Look at `TROUBLESHOOTING_AND_LESSONS.md`
5. **Verify no Manus tasks:** Check Manus dashboard

### Files Manus Will Need

- `README_MASTER.md` - Project overview
- `LAUNCHAGENT_SETUP.md` - LaunchAgent reference
- `SCRIPT_DEPLOYMENT_TEMPLATE.md` - Deployment checklist
- `TROUBLESHOOTING_AND_LESSONS.md` - Known issues
- `scripts/shared_utils.py` - Common functions
- `blueprints/*.json` - Original Make.com blueprints

## Contact & Support

### Internal Issues
- Check `TROUBLESHOOTING_AND_LESSONS.md`
- Review logs: `~/Automations/logs/`
- Test script manually

### Manus Support
- Issue: Duplicate tasks or unexpected charges
- Contact: https://manus.im/feedback
- Reference: Previous conversation link in support request

## Version History

| Date | Version | Status | Notes |
|------|---------|--------|-------|
| 2026-03-21 | 1.0 | Active | Scripts 1 & 7 deployed, LaunchAgent setup complete |
| | | | Resolved duplicate task crisis |
| | | | Created comprehensive documentation |

## Next Steps

1. ✅ Script 1 (Google Sheets → Airtable) - ACTIVE
2. ✅ Script 7 (Gmail AI Qualification) - ACTIVE
3. ⏳ Script 2 (Send Qualification Email) - Next
4. ⏳ Script 3 (Calendar Invite) - After Script 2
5. ⏳ Scripts 4-6, 8-11 - Continue in order
6. 📋 Master deployment summary - When all scripts complete

## Questions?

Refer to:
1. **Project structure:** This README
2. **LaunchAgent setup:** `LAUNCHAGENT_SETUP.md`
3. **Deployment process:** `SCRIPT_DEPLOYMENT_TEMPLATE.md`
4. **Troubleshooting:** `TROUBLESHOOTING_AND_LESSONS.md`
5. **Script details:** Individual script comments
6. **Common functions:** `shared_utils.py`

---

**Last Updated:** 2026-03-21  
**Maintained By:** Manus AI Agent  
**Project:** Local Automations – Make.com Migration  
**Status:** 🟢 Active & Monitored
