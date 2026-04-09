# Meraglim Holdings — Local Automations Master README

## Project Overview

This project converts 12 Make.com automation blueprints into persistent local Python scripts that run on macOS using LaunchAgents. All scripts execute locally with zero Manus involvement, preventing unexpected charges and ensuring reliability.

**Status:** 🟢 Active — Scripts 1–9, 10T, MHC10, MHC10T, MHC11 deployed and verified; Scripts 6 & 8 fixed and verified  
**Cost:** $0 — All automation runs locally on your Mac  
**Last Updated:** April 8, 2026

---

## ⚠️ New Agent Onboarding

**If you are a Manus agent starting a new task, do not rely on this README for script status.** Pull the latest docs from GitHub first (the opening prompt handles this automatically), then read `SCRIPTS_REGISTRY.md` as the single source of truth for all script statuses.

---

## Current Script Status

| Script | Name | Status | Notes |
|--------|------|--------|-------|
| Script 0 | Daily Log Analysis | ✅ ACTIVE | Runs at 6 AM; handles Script 7 comma-millisecond timestamp format |
| Script 1 | Google Sheets → Airtable | ✅ ACTIVE | Every 5 min via LaunchAgent |
| Script 2 | Airtable → Qualification Email | ✅ ACTIVE | Every 15 min via LaunchAgent |
| Script 3 | Qualified Prospect → Calendar Invite | ✅ ACTIVE | LaunchAgent |
| Script 4 | Not Qualified → Polite Decline | ✅ ACTIVE | Every 15 min via LaunchAgent |
| Script 5 | No Response → 7-Day Follow-Up | ✅ ACTIVE | Uses google_token.json; correct Airtable field names |
| Script 6 | Qualified Prospect → ClickUp Deal | ✅ FIXED | Filter formula fixed (Make.com TRUE()/FALSE() → Airtable 1/0); deduplication added |
| Script 7 | Gmail Reply → AI Qualification | ✅ ACTIVE | Every 5 min; comma-millisecond timestamps handled by Script 0 |
| Script 8 | Meeting Scheduled → ClickUp Prep | ✅ FIXED | Same filter formula fix as Script 6; deduplication added |
| Script 9 | Clay Enrichment Webhook | ✅ ACTIVE | Flask server on port 8000; receives Clay POSTs |
| Script 10T | Meeting Intelligence Trigger | ✅ ACTIVE | Webhook-triggered; event-driven |
| MHC10 | Meeting Intelligence Sync | ✅ ACTIVE | Event-driven |
| MHC10T | Meeting Intelligence Trigger (MHC) | ✅ ACTIVE | Event-driven |
| MHC11 | Post-Meeting Intelligence Sync | ✅ ACTIVE | Fully integrated: Gmail + Claude + Airtable + ClickUp; INTERNAL path testing pending |

---

## Infrastructure

| Service | Status | Details |
|---------|--------|---------|
| Cloudflare Tunnel | ✅ Running | LaunchAgent `com.meraglim.cloudflared-tunnel`; 4 connections to ATL edge nodes |
| script10t.meraglim.com | ✅ Healthy | Routes to localhost:8000; `/health` endpoint confirmed |
| Script 9 Webhook | ✅ Running | Flask on port 8000; LaunchAgent `com.meraglim.script09-clay-webhook` |
| Script 11 LaunchAgent | ✅ Deployed | `com.meraglim.script11-post-meeting-intelligence`; installed via deployment script |
| `.env` | ✅ 34 entries | Includes ANTHROPIC_API_KEY; loaded via explicit absolute path in shared_utils.py |
| GitHub Repo | ✅ Public | https://github.com/kwmassengill/automation; auto-pushed at session close |

---

## Session Handoff Workflow

### Starting a New Task

Paste the opening prompt from `~/Automations/docs/STANDARD_OPENING_PROMPT.md`. The agent will pull all 5 docs from GitHub automatically — no file attachments needed.

### Closing a Session

Paste the close protocol from `~/Automations/docs/SESSION_CLOSE_PROTOCOL.md`. The agent updates all 5 docs, uploads to CDN, and provides the `session_close.sh` command. Running that command saves docs to Mac and pushes to GitHub.

---

## Quick Start Commands

```bash
# Check all script LaunchAgents
launchctl list | grep com.meraglim

# View real-time logs
tail -f ~/Automations/logs/script_11.log

# Check Cloudflare tunnel health
curl -s https://script10t.meraglim.com/health

# Stop all scripts
for plist in ~/Library/LaunchAgents/com.meraglim.*.plist; do launchctl unload "$plist"; done

# Start all scripts
for plist in ~/Library/LaunchAgents/com.meraglim.*.plist; do launchctl load "$plist"; done
```

---

## Platform Context

- **Mac:** Apple Silicon MacBook Pro, username: kevinmassengill
- **Python:** /usr/bin/python3 (3.9) — all scripts must use Python 3.9-compatible syntax
- **Homebrew:** /opt/homebrew/bin/ (NOT /usr/local/bin/)
- **LaunchAgents:** ~/Library/LaunchAgents/com.meraglim.*
- **Google OAuth:** All scripts use `google_token.json` (never `oauth_token.json`)
- **Credentials:** ~/Automations/config/.env (34 entries; loaded via explicit absolute path)
- **GitHub:** https://github.com/kwmassengill/automation (public; PAT in macOS Keychain)

---

## Open Items

| Item | Priority | Added |
|------|----------|-------|
| Test Script 11 INTERNAL email path (internal meeting transcript processing) | High | April 8, 2026 |
| Monitor Scripts 6 & 8 for 24–48 hours to confirm no duplicate ClickUp tasks | Medium | April 8, 2026 |
| Clay webhook URL in Clay's UI still needs to be pointed to `https://script10t.meraglim.com/clay-webhook` | Medium | April 8, 2026 |

---

**Maintained By:** Manus AI Agent  
**Project:** Local Automations — Make.com Migration
