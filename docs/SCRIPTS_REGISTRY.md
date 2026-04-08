# Local Automations - Master Scripts Registry

This registry is the **single source of truth** for all automation scripts in the Make.com Migration project. 

**CRITICAL INSTRUCTION FOR MANUS AGENTS:** 
Whenever you start a new task in this project, you MUST read this file first to understand which scripts exist, which are active, and which still need to be built. Do not rely on other README files for script status, as they may be outdated.

## 1. Project Architecture & File Locations

All scripts share a common infrastructure to ensure consistency, reliability, and prevent duplicate processing.

### Directory Structure
The project uses a standardized directory structure on the user's Mac (`~/Automations/`), which Manus accesses via `/mnt/desktop/Make Blueprints/Automations/`.

*   **Scripts Directory:** `~/Automations/scripts/`
    *   Contains all executable Python scripts (`script_XX_description.py`).
    *   Contains `shared_utils.py` (logging, state management, error handling).
*   **Configuration Directory:** `~/Automations/config/`
    *   Contains `.env` (API keys and credentials - **NEVER COMMIT**).
    *   Contains `state.db` (SQLite database tracking execution state and preventing duplicates).
*   **Logs Directory:** `~/Automations/logs/`
    *   Contains per-script log files (`script_XX_YYYYMMDD.log`).
*   **Blueprints Directory:** `~/Automations/blueprints/`
    *   Contains the original Make.com JSON exports for reference.

### Shared Infrastructure (`shared_utils.py`)
Every script MUST import and use the shared utilities:
1.  **Logging:** `setup_logger(SCRIPT_NAME)` creates standardized file and console logs.
2.  **State Management:** `StateManager()` interacts with `state.db` to track the `last_processed_id` and prevent duplicate runs.
3.  **Error Handling:** The `@handle_errors` decorator automatically catches exceptions, logs them, and sends email notifications.

## 2. Master Script Inventory

This table tracks the definitive status of all 20+ planned scripts. 

| ID | Script Name / Purpose | Python Filename | Status | Trigger / Schedule | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | Google Sheets to Airtable Sync | `script_01_google_sheets_to_airtable.py` | ✅ **ACTIVE** | LaunchAgent (5 min) | Google Sheets API, Airtable API |
| **02** | Airtable New Prospect → Send Qualification Email | `script_02_airtable_qualification_email_oauth.py` | ✅ **ACTIVE** | LaunchAgent (15 min) | Airtable API, Gmail OAuth 2.0 |
| **03** | Qualified Prospect - Calendar Invite | `script_03_qualified_prospect_calendar_invite.py` | ✅ **ACTIVE** | LaunchAgent | Airtable API, Google Calendar API |
| **04** | Not Qualified - Polite Decline | `script_04_not_qualified_polite_decline_oauth.py` | ✅ **ACTIVE** | LaunchAgent (15 min) | Airtable API, Gmail OAuth 2.0 |
| **05** | No Response - 7 Day Follow Up | `script_05_no_response_7_day_followup_oauth.py` | ✅ **ACTIVE** | LaunchAgent (15 min) | Airtable API, Gmail OAuth 2.0 |
| **06** | Qualified Prospect → ClickUp Deal Pipeline | `script_06_qualified_prospect_clickup_deal.py` | ⚠️ **NEEDS FIX** (Filter Formula) | LaunchAgent | Airtable API, ClickUp API |
| **07** | Gmail Reply → AI Qualification | `script_07_gmail_reply_ai_qualification.py` | ✅ **ACTIVE** | LaunchAgent (5 min) | Gmail API, OpenAI API, Airtable API |
| **08** | Meeting Scheduled → ClickUp Prep Task | `script_08_meeting_scheduled_clickup_prep.py` | ⚠️ **NEEDS FIX** (Filter Formula) | LaunchAgent | Google Calendar API, ClickUp API |
| **09** | Clay Enrichment Webhook → Airtable | `script_09_clay_enrichment_webhook_airtable.py` | ✅ **ACTIVE** | LaunchAgent (Port 8000 Webhook) | Airtable API |
| **10T** | Meeting Intelligence Trigger | `script_mhc10t_meeting_intelligence_trigger.py` | ✅ **ACTIVE** | LaunchAgent | Calendar/Meeting API |
| **10** | Meeting Intelligence Sync | `script_mhc10_meeting_intelligence_sync.py` | ✅ **ACTIVE** | LaunchAgent | Meeting API, Airtable/ClickUp |
| **11** | Post-Meeting Intelligence Sync | `script_mhc11_post_meeting_intelligence_sync.py` | ✅ **ACTIVE** | LaunchAgent | Meeting API, AI Processing |

**Status Legend:**
- ✅ **ACTIVE**: Script is built, deployed, and running successfully via LaunchAgent
- ⚠️ **NEEDS TESTING**: Script is built and deployed but requires testing/verification
- 🔄 **TESTING**: Script is built and currently in final testing phase
- ❌ **SKIPPED**: Script was intentionally not implemented

**Note:** All ACTIVE scripts are currently running via macOS LaunchAgents. Script 4 needs immediate testing to verify it's working correctly.

## 3. Standard Operating Procedures for New Tasks

When a user requests to build a new script (e.g., "Let's build Script 10"), follow this exact process to ensure continuity:

1.  **Verify Status:** Check this registry to confirm the script's ID and current status.
2.  **Review Blueprint:** Read the corresponding JSON blueprint in the `blueprints/` directory to understand the exact logic Make.com was using.
3.  **Scaffold Script:** Create the new Python file in `scripts/` using the standard naming convention (`script_XX_description.py`).
4.  **Implement Shared Utils:** Import `setup_logger`, `StateManager`, and `@handle_errors` from `shared_utils.py`.
5.  **Build Logic:** Implement the API calls and business logic, ensuring you use `StateManager` to track progress and prevent duplicate actions.
6.  **Test Locally:** Run the script manually to verify it works and logs correctly.
7.  **Deploy:** Create the LaunchAgent `.plist` file following the instructions in `LAUNCHAGENT_SETUP.md`.
8.  **Update Registry:** Change the script's status in this `SCRIPTS_REGISTRY.md` file from PENDING to ACTIVE.

By strictly adhering to this registry and process, we guarantee that no work is lost between sessions and every script integrates perfectly into the existing local automation ecosystem.
