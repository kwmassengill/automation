# Session Close Protocol
## Meraglim Local Automations — Make.com Migration Project

This document defines the standardized procedure for closing every work session. It ensures all changes are captured and pushed to GitHub so the next session starts with a complete and accurate picture of the system.

**Last Updated:** April 8, 2026 — Updated to reflect GitHub-based sync workflow (tested and confirmed working).

---

## The Session Close Prompt

Copy and paste this prompt at the end of every session:

---

> Session is closing. Please do the following in order:
>
> **1. Update all 5 documentation files** to reflect everything completed this session:
> - `README_MASTER.md` — update script status table and current state summary
> - `SCRIPTS_REGISTRY.md` — update status, notes, and known issues for any scripts touched
> - `INFRASTRUCTURE_SUMMARY.md` — update if any services, ports, tunnels, or LaunchAgents changed
> - `TROUBLESHOOTING_AND_LESSONS.md` — append a new dated entry summarizing issues encountered and resolutions
> - `SESSION_CLOSE_PROTOCOL.md` — update only if the close workflow itself changed
>
> **Important:** Before writing updates, pull the current versions of all 5 files from GitHub using:
> ```bash
> for file in README_MASTER.md SCRIPTS_REGISTRY.md INFRASTRUCTURE_SUMMARY.md TROUBLESHOOTING_AND_LESSONS.md SESSION_CLOSE_PROTOCOL.md; do
>   curl -fsSL "https://raw.githubusercontent.com/kwmassengill/automation/main/docs/$file" -o "/tmp/$file"
> done
> ```
> Read all 5 files before writing any updates to ensure accuracy.
>
> **2. Upload all 5 updated files to CDN** using `manus-upload-file`.
>
> **3. Provide the `session_close.sh` command** in this exact format, substituting the real CDN URLs:
> ```bash
> bash ~/Automations/scripts/session_close.sh \
>   --readme    "[README_MASTER.md CDN URL]" \
>   --registry  "[SCRIPTS_REGISTRY.md CDN URL]" \
>   --infra     "[INFRASTRUCTURE_SUMMARY.md CDN URL]" \
>   --trouble   "[TROUBLESHOOTING_AND_LESSONS.md CDN URL]" \
>   --protocol  "[SESSION_CLOSE_PROTOCOL.md CDN URL]" \
>   --qr-date   "$(date '+%Y-%m-%d')"
> ```
>
> Running this command on my Mac will download all updated docs to `~/Automations/docs/` and push everything to GitHub automatically.

---

## What Each File Captures

| File | Purpose | Update When |
|------|---------|-------------|
| `README_MASTER.md` | High-level project overview and script status table | Any script status changes; infrastructure changes |
| `SCRIPTS_REGISTRY.md` | Master inventory — single source of truth for all scripts | Any script built, fixed, renamed, or has trigger/dependencies changed |
| `INFRASTRUCTURE_SUMMARY.md` | Architecture documentation for services, tunnels, LaunchAgents | Any new LaunchAgent, tunnel, webhook server, or service added or changed |
| `TROUBLESHOOTING_AND_LESSONS.md` | Dated log of issues, root causes, and resolutions | Any time a script fails, a bug is found, or a non-obvious fix is applied |
| `SESSION_CLOSE_PROTOCOL.md` | This file — the close workflow itself | Only when the close workflow changes |

---

## What session_close.sh Does

When you run the `session_close.sh` command on your Mac, it:

1. Downloads all updated docs from CDN to `~/Automations/docs/`
2. Runs `git add docs/ scripts/` in `~/Automations/`
3. Commits with a timestamped message
4. Pushes to `https://github.com/kwmassengill/automation` (main branch)

The PAT is stored in macOS Keychain — no password prompt. The push is fully automatic.

---

## Additional Health Checks at Session Close

```bash
# All LaunchAgents
launchctl list | grep com.meraglim

# Cloudflare tunnel
tail -3 ~/Automations/logs/cloudflared_tunnel_error.log

# Script 9 / 10T webhook health
curl -s https://script10t.meraglim.com/health

# .env key count (should be 33)
grep -c "=" ~/Automations/config/.env

# Recent log activity
ls -lt ~/Automations/logs/ | head -15
```

---

## Open Items Tracking

At session close, unresolved items should be noted in `README_MASTER.md` under the "Open Items" section in this format:

| Item | Priority | Added |
|------|----------|-------|
| Description of open item | High / Medium / Low | Date |

---

**Protocol Created:** April 8, 2026  
**Last Updated:** April 8, 2026  
**Maintainer:** Manus AI Agent  
**Project:** Local Automations — Make.com Migration
