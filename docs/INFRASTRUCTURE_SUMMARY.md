# Meraglim Holdings - Infrastructure Summary

This document outlines the infrastructure and services used in the Make.com migration project.

## Core Infrastructure

| Component | Description | Status | Notes |
|-----------|-------------|--------|-------|
| **macOS Host** | Local machine running all automations | ✅ Active | Primary execution environment |
| **LaunchAgents** | macOS native scheduling system | ✅ Active | Replaces Make.com scheduling |
| **Python 3.9+** | Script execution environment | ✅ Active | Standard library + requests |
| **SQLite** | Local state tracking database | ✅ Active | `~/Automations/config/state.db` |

## External Services & APIs

| Service | Purpose | Authentication | Status |
|---------|---------|----------------|--------|
| **Airtable** | Primary data store for prospects | API Key (`AIRTABLE_API_KEY`) | ✅ Active |
| **Google Sheets** | Lead source | OAuth Token (`GOOGLE_TOKEN_FILE`) | ✅ Active |
| **Gmail** | Email monitoring and sending | MCP Integration | ✅ Active |
| **OpenAI** | AI qualification and intelligence | API Key (`OPENAI_API_KEY`) | ✅ Active |
| **ClickUp** | Task and deal management | API Key (`CLICKUP_API_KEY`) | ✅ Active |
| **Clay** | Data enrichment | API Key (`CLAY_API_KEY`) | ⏳ Pending |

## Active LaunchAgents

| Agent Name | Script | Schedule | Status |
|------------|--------|----------|--------|
| `com.meraglim.script01` | `script_01_google_sheets_to_airtable.py` | Every 5 mins | ✅ Loaded |
| `com.meraglim.script06` | `script_06_qualified_prospect_clickup_deal.py` | Every 5 mins | ✅ Loaded |
| `com.meraglim.script07` | `script_07_gmail_reply_ai_qualification.py` | Every 5 mins | ✅ Loaded |
| `com.meraglim.script08` | `script_08_meeting_scheduled_clickup_prep.py` | Every 5 mins | ✅ Loaded |

## Recent Infrastructure Changes

### 2026-04-08
- **LaunchAgents:** Reloaded `com.meraglim.script06` and `com.meraglim.script08` to apply deduplication filter fixes.
- **ClickUp Integration:** Verified ClickUp API connectivity and task creation capabilities for Scripts 6 and 8.

---
**Last Updated:** 2026-04-08
