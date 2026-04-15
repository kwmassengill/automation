# AGENTS.md — Meraglim Automation Stack
## Claude Code Operational Reference

**Read this file before touching any script, file, or configuration in this repository.**
**Last Updated:** April 15, 2026
**Maintained By:** Claude Code (implementation) / Claude Projects (strategic coordination)

---

## What This File Is

AGENTS.md is the sixth canonical document in the Meraglim session architecture. It serves as the Claude Code-specific companion to the five GitHub docs. At the start of every Claude Code session, read all six documents in this order:
1. This file (AGENTS.md)
2. README_MASTER.md
3. SCRIPTS_REGISTRY.md
4. INFRASTRUCTURE_SUMMARY.md
5. TROUBLESHOOTING_AND_LESSONS.md
6. SESSION_CLOSE_PROTOCOL.md

Do not create a plan or take any action until all six are read.

---

## Business Context

Meraglim Holdings Corporation is a Delaware C-Corp acquisition holding company. Operator: Kevin Massengill, Chairman and CEO. The automation stack supports one function: identifying, qualifying, and closing acquisitions of lower middle market companies ($500K-$10M EBITDA) in cybersecurity, defense technology, and data solutions via the Annuity Sale model (IRC Section 453 installment sale, no cash at closing, 30-day close).

---

## Repository Structure

    ~/Automations/
    config/
        .env                          # 34 API keys — never commit, never hardcode
        google_token.json             # Google OAuth — never commit
    docs/
        AGENTS.md                     # This file
        README_MASTER.md              # Executive dashboard + script status table
        SCRIPTS_REGISTRY.md           # Single source of truth for all scripts
        INFRASTRUCTURE_SUMMARY.md     # Services, tunnels, LaunchAgents
        TROUBLESHOOTING_AND_LESSONS.md
        SESSION_CLOSE_PROTOCOL.md
    logs/                             # Runtime logs — never commit
    scripts/
        shared_utils.py
        session_close.sh
        requirements.txt
        script_00 through script_mhc11

---

## Platform Constants — Never Deviate

| Parameter | Value |
|-----------|-------|
| Python | /usr/bin/python3 (3.9) |
| Python syntax | Optional[X] from typing — never X or None (3.10+ only) |
| Homebrew | /opt/homebrew/bin/ — never /usr/local/bin/ |
| Google OAuth token | google_token.json — never oauth_token.json |
| .env loading | Always load_dotenv("/Users/kevinmassengill/Automations/config/.env") |
| LaunchAgent prefix | com.meraglim.* |
| LaunchAgents directory | ~/Library/LaunchAgents/ |
| Logs directory | ~/Automations/logs/ with ISO timestamp prefixes |
| Claude model | claude-sonnet-4-20250514 |
| Airtable base | appoNkgoKHAUXgXV9 |
| Airtable table | tblxEhVek8ldTQMW1 |

---

## Script Inventory and Status

| Script | Canonical Filename | Status | Trigger | Notes |
|--------|-------------------|--------|---------|-------|
| Script 0 | script_00_daily_log_analysis_native.py | ACTIVE | 6 AM daily | Health reporting |
| Script 1 | script_01_google_sheets_to_airtable.py | ACTIVE | Every 5 min | Duplicate prevention by email |
| Script 2 | script_02_airtable_qualification_email.py | ACTIVE | Every 15 min | MAX_EMAILS_PER_RUN=5; filter uses 1/0 not TRUE()/FALSE() |
| Script 3 | script_03_qualified_prospect_calendar_invite.py | ACTIVE | Every 15 min | Triggers on Qualification Status = Qualified; updates to Calendar Invite Sent |
| Script 4 | script_04_not_qualified_polite_decline.py | ACTIVE | Every 15 min | Gmail OAuth |
| Script 5 | script_05_no_response_7_day_followup.py | ACTIVE | Every 15 min | Fields: Qualification Status, Date Sent, Days Since Email |
| Script 6 | script_06_qualified_prospect_clickup.py | FIXED | LaunchAgent | Filter uses 1/0; deduplication via ClickUp Task Created != 1 |
| Script 7 | script_07_gmail_reply_ai_qualification.py | ACTIVE | Every 5 min | JSON parsing confirmed working in Python version |
| Script 8 | script_08_meeting_scheduled_clickup.py | FIXED | LaunchAgent | Same filter fix as Script 6 |
| Script 9 | script_09_clay_enrichment_webhook_airtable.py | ACTIVE | Flask port 8000 | Clay UI webhook URL still needs updating |
| Script 10T | script_10t_meeting_intelligence_trigger.py | ACTIVE | Webhook | Public URL: script10t.meraglim.com |
| MHC10 | script_10_pre_meeting_intelligence.py | ACTIVE | Event-driven | Manual trigger via reqbin.com |
| MHC10T | script_mhc10t_meeting_intelligence_trigger.py | ACTIVE | Event-driven | MHC variant |
| MHC11 | script_mhc11_post_meeting_intelligence_sync.py | ACTIVE | Every 5 min | External path verified; INTERNAL path untested |

---

## Open Items

| Item | Priority | Added |
|------|----------|-------|
| Test Script 11 INTERNAL email path | High | April 8, 2026 |
| Update Clay webhook URL in Clay UI | Medium | April 8, 2026 |

---

## Critical Rules

### Never Do This
- Modify a production script without first creating a .bak copy
- Use bare load_dotenv() — always specify absolute path
- Use X or None type hints — use Optional[X] from typing
- Reference /usr/local/bin/ — Homebrew is at /opt/homebrew/bin/
- Reference oauth_token.json — correct file is google_token.json
- Hardcode any credential, API key, or token
- Install new pip packages without confirming with Kevin first
- Commit .env, google_token.json, or any file in logs/
- Write to Airtable live records without testing against a test record first
- Assume field names from Make.com blueprints exist in Airtable — always verify

### Always Do This
- Read all six docs before creating any plan or taking any action
- Verify plist exists and log file created within one poll cycle after any deployment
- Fetch one Airtable record and print all field names before writing any new filter or update
- Test Airtable writes against a test record first
- Preserve the raw JSON return instruction at end of every Claude API system prompt
- Log to ~/Automations/logs/ with ISO timestamp prefixes
- Append a note to this file under Fix Log after any successful fix
- Run session close protocol at end of every task session

---

## Known Technical Constraints

Airtable boolean filters: Use 1/0 — never TRUE()/FALSE(). Make.com syntax is not valid in Airtable REST API.

Airtable field names: Never assume blueprint field names exist. Always verify with a one-record fetch before writing filters or updates.

reqbin.com JSON payloads: Use pipe delimiters instead of newlines. No internal double quotes in full_briefing_text.

Claude API calls: Use Map mode. JSON string body mode fails with special characters. Every system prompt must end with instruction to return raw JSON without markdown fences.

LaunchAgent .env loading: Always use explicit absolute path. Bare load_dotenv() fails silently when run as LaunchAgent.

Webhook receivers: Any script receiving external data must be a Flask HTTP server, not a polling script.

Python 3.9 type hints: Use Optional[X] from typing — never X or None syntax.

Cloudflare tunnel DNS: CNAME must be Proxied (orange cloud) — DNS only bypasses the tunnel.

Gmail attachment size field: Use part.get("size", 0) — not part["size"].

Airtable date fields: Send YYYY-MM-DD format only — not ISO datetime.

MHC-11 prospect email extraction: Use regex — not Make.com .com-boundary substring logic.

ClickUp task ID extraction: Use last(split(URL; "/")) from stored ClickUp task URL in Airtable.

---

## ClickUp Reference

| List | ID |
|------|----|
| Meeting Intelligence | 901711612948 |
| Next Actions | 901711661107 |
| Meeting Summaries | 901711661162 |

---

## Session Close Protocol

1. Update any docs that changed this session
2. Append fix notes to this file under Fix Log
3. Run from terminal:
   cd ~/Automations
   git add docs/ scripts/
   git commit -m "YYYY-MM-DD HH:MM session close — description"
   git push
4. Confirm push succeeded before ending session

---

## Two-Agent Architecture

Claude Projects — Strategic layer. Architectural decisions, sequencing, documentation drafting. Accesses GitHub via web_fetch. Cannot execute bash or write to Mac directly.

Claude Code — Implementation layer. Direct filesystem access, executes scripts, reads logs, edits in place, commits to GitHub. Reads AGENTS.md and five docs to reconstruct context each session.

When Claude Code encounters an ambiguous architectural decision: check this file first, then TROUBLESHOOTING_AND_LESSONS.md, then escalate to Kevin.

---

## Fix Log

### April 15, 2026
- Scripts 2, 3, 4, 5, 7, 8: Created missing LaunchAgent plist files. All six scripts were never running since Mac migration despite being marked ACTIVE in README.
- Script 2: Fixed filter formula TRUE() to 1. Raised MAX_EMAILS_PER_RUN from 1 to 5.
- Script 3: Fixed filter formula FALSE() to 0. Replaced nonexistent Calendar Invite Sent field with Qualification Status update pattern. Filter triggers on Qualification Status = Qualified, updates to Calendar Invite Sent after sending.
- Script 5: Removed legacy misnamed plist com.meraglim.script05_no_response_7day_followup. Created clean com.meraglim.script05 plist.
- Script 7: Confirmed operational — JSON parsing issue from Make.com version was resolved in Python migration.
- Rules added: Plist verification required after every deployment. Airtable field names must be verified by one-record fetch before any new filter or update is written.
