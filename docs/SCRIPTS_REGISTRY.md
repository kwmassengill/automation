# Meraglim Holdings — Scripts Registry

This registry is the **single source of truth** for all automation scripts. Read this file first at the start of every task before taking any action.

**Last Updated:** April 8, 2026

---

## Master Script Inventory

| ID | Purpose | Canonical Filename | Status | Trigger | Notes |
|:---|:--------|:------------------|:-------|:--------|:------|
| 00 | Daily Log Analysis & Health Report | `script_00_daily_log_analysis_native.py` | ✅ ACTIVE | LaunchAgent — 6 AM daily | Handles Script 7 comma-millisecond timestamp format (`2026-04-08 09:36:45,316`) |
| 01 | Google Sheets → Airtable Sync | `script_01_google_sheets_to_airtable.py` | ✅ ACTIVE | LaunchAgent — every 5 min | Duplicate prevention by email; processes 10 rows/run |
| 02 | Airtable New Prospect → Qualification Email | `script_02_airtable_qualification_email.py` | ✅ ACTIVE | LaunchAgent — every 15 min | Gmail OAuth via google_token.json |
| 03 | Qualified Prospect → Calendar Invite | `script_03_qualified_prospect_calendar_invite.py` | ✅ ACTIVE | LaunchAgent | Google Calendar API |
| 04 | Not Qualified → Polite Decline Email | `script_04_not_qualified_polite_decline.py` | ✅ ACTIVE | LaunchAgent — every 15 min | Gmail OAuth via google_token.json |
| 05 | No Response → 7-Day Follow-Up Email | `script_05_no_response_7_day_followup.py` | ✅ ACTIVE | LaunchAgent — every 15 min | Uses google_token.json; Airtable fields: {Qualification Status}, {Date Sent}, {Days Since Email} |
| 06 | Qualified Prospect → ClickUp Deal Pipeline | `script_06_qualified_prospect_clickup.py` | ✅ FIXED | LaunchAgent | Filter formula fixed: Make.com `TRUE()`/`FALSE()` → Airtable `1`/`0`; `{ClickUp Task Created} != 1` deduplication added |
| 07 | Gmail Reply → AI Qualification | `script_07_gmail_reply_ai_qualification.py` | ✅ ACTIVE | LaunchAgent — every 5 min | Claude/OpenAI for qualification; marks emails read after processing |
| 08 | Meeting Scheduled → ClickUp Prep Task | `script_08_meeting_scheduled_clickup.py` | ✅ FIXED | LaunchAgent | Same filter formula fix as Script 6; `{ClickUp Task Created} != 1` deduplication added |
| 09 | Clay Enrichment Webhook → Airtable | `script_09_clay_enrichment_webhook_airtable.py` | ✅ ACTIVE | Flask webhook — port 8000 (persistent LaunchAgent) | Clay POSTs to `https://script10t.meraglim.com/clay-webhook`; Clay UI webhook URL still needs updating |
| 10T | Meeting Intelligence Trigger | `script_10t_meeting_intelligence_trigger.py` | ✅ ACTIVE | Webhook-triggered; event-driven | Public URL: script10t.meraglim.com |
| 10 | Pre-Meeting Intelligence | `script_10_pre_meeting_intelligence.py` | ✅ ACTIVE | Event-driven | Triggered by Script 10T |
| MHC10 | Meeting Intelligence Sync | `script_mhc10_meeting_intelligence_sync.py` | ✅ ACTIVE | Event-driven | MHC variant |
| MHC10T | Meeting Intelligence Trigger (MHC) | `script_mhc10t_meeting_intelligence_trigger.py` | ✅ ACTIVE | Event-driven | MHC variant |
| MHC11 | Post-Meeting Intelligence Sync | `script_mhc11_post_meeting_intelligence_sync.py` | ✅ ACTIVE | Event-driven | MHC variant |

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ ACTIVE | Built, deployed, running successfully via LaunchAgent |
| ✅ FIXED | Previously broken; fix deployed and verified |
| ⚠️ NEEDS FIX | Known issue identified; fix pending |
| 📭 NO ACTIVITY | Event-driven; no activity is expected and normal |
| ❌ BROKEN | Failing; requires immediate attention |

---

## Canonical Infrastructure Files

| File | Location | Purpose |
|------|----------|---------|
| `shared_utils.py` | `~/Automations/scripts/` | Shared utilities; loads .env from explicit absolute path |
| `session_close.sh` | `~/Automations/scripts/` | Session close: downloads updated docs from CDN + pushes to GitHub |
| `.env` | `~/Automations/config/` | All API keys (33 entries); NEVER commit |
| `google_token.json` | `~/Automations/config/` | Google OAuth token; used by all Gmail/Calendar scripts |
| `setup_google_auth.py` | `~/Automations/scripts/` | Re-run to refresh Google OAuth token if expired |
| `setup_cron_jobs.sh` | `~/Automations/scripts/` | Legacy setup reference |
| `requirements.txt` | `~/Automations/scripts/` | Python package dependencies |

---

## Critical Rules for All Scripts

1. **Python 3.9 compatibility required** — use `Optional[X]` from `typing`, never `X | None` syntax
2. **Always use `google_token.json`** — never `oauth_token.json`
3. **Homebrew path is `/opt/homebrew/bin/`** — never `/usr/local/bin/` (Apple Silicon Mac)
4. **`shared_utils.py` loads `.env` from explicit absolute path** — never use bare `load_dotenv()`
5. **Webhook receivers must be Flask HTTP servers** — never polling scripts (Clay, Make.com webhooks push; they do not expose polling APIs)
6. **Airtable filter syntax uses `1`/`0`** — never Make.com `TRUE()`/`FALSE()` syntax

---

## Standard Procedure for New Tasks

1. Pull latest docs from GitHub (opening prompt handles this)
2. Read this registry to confirm current script statuses
3. Read `TROUBLESHOOTING_AND_LESSONS.md` for known issues
4. Perform the requested work
5. Update this registry if any script status changes
6. Run session close protocol at end of task

---

**Maintained By:** Manus AI Agent  
**Project:** Local Automations — Make.com Migration  
**GitHub:** https://github.com/kwmassengill/automation
