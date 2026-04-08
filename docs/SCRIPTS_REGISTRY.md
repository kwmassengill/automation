# Meraglim Holdings - Scripts Registry

This document maintains a complete inventory of all automation scripts in the Make.com migration project.

## Active Scripts

| Script ID | Name | Status | Last Updated | Notes |
|-----------|------|--------|--------------|-------|
| Script 01 | `script_01_google_sheets_to_airtable.py` | ✅ Active | 2026-03-21 | Syncs Google Sheets leads to Airtable. Uses state.db for tracking. |
| Script 06 | `script_06_qualified_prospect_clickup_deal.py` | ✅ Active | 2026-04-08 | Creates ClickUp deal for qualified prospects. Fixed deduplication filter. |
| Script 07 | `script_07_gmail_reply_ai_qualification.py` | ✅ Active | 2026-03-21 | Monitors Gmail for replies and uses AI to qualify prospects. |
| Script 08 | `script_08_meeting_scheduled_clickup_prep.py` | ✅ Active | 2026-04-08 | Creates prep task in ClickUp when meeting is scheduled. Fixed deduplication filter. |

## Pending Scripts

| Script ID | Name | Status | Target Date | Notes |
|-----------|------|--------|-------------|-------|
| Script 02 | `script_02_airtable_qualification_email.py` | ⏳ Pending | TBD | Sends qualification email to new prospects. |
| Script 03 | `script_03_qualified_prospect_calendar_invite.py` | ⏳ Pending | TBD | Creates calendar invite for qualified prospects. |
| Script 04 | `script_04_not_qualified_polite_decline.py` | ⏳ Pending | TBD | Sends polite decline to not-qualified prospects. |
| Script 05 | `script_05_qualified_7day_followup.py` | ⏳ Pending | TBD | Sends 7-day follow-up email. |
| Script 09 | `script_09_mhc10_meeting_intelligence_trigger.py` | ⏳ Pending | TBD | Triggers meeting intelligence on meeting start. |
| Script 10 | `script_10_mhc10_meeting_intelligence_summary.py` | ⏳ Pending | TBD | Generates meeting intelligence summary. |
| Script 11 | `script_11_mhc11_post_meeting_intelligence.py` | ⏳ Pending | TBD | Post-meeting intelligence processing. |

## Known Issues & Resolutions

### Script 06 & 08: Duplicate Task Creation
- **Issue:** Scripts were creating duplicate ClickUp tasks on every run.
- **Root Cause:** Missing deduplication filters in Airtable queries. Used Make.com syntax (`TRUE()`, `FALSE()`) instead of Airtable native syntax (`1`, `0`).
- **Resolution:** Added `{ClickUp Task Created} != 1` to the filter formulas in both scripts.
- **Date Resolved:** 2026-04-08

---
**Last Updated:** 2026-04-08
