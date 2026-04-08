# Session Close Protocol
## Meraglim Local Automations — Make.com Migration Project

This document defines the standardized procedure for closing every work session in this project. It ensures that all knowledge, fixes, and changes are captured before the session ends, so the next session starts with a complete and accurate picture of the system.

---

## The Session Close Prompt

Copy and paste this prompt at the end of every session:

---

> **SESSION CLOSE PROTOCOL — Execute these exact steps to close the session:**
>
> **Step 1: Update Documentation Files**
> Read the current versions of these 5 files from your sandbox (either from the project directory or files I attached), update them to reflect today's work, and save them:
> 1. `README_MASTER.md` (Update script statuses)
> 2. `SCRIPTS_REGISTRY.md` (Update inventory table)
> 3. `INFRASTRUCTURE_SUMMARY.md` (Document new services/architecture)
> 4. `TROUBLESHOOTING_AND_LESSONS.md` (Add dated entry for issues/resolutions)
> 5. `SCRIPTS_QUICK_REFERENCE_MERAGLIM_FORMAT_[Date].docx` (Update script entries, save as new dated version)
>
> **Step 2: Upload to CDN**
> Use the `manus-upload-file` tool to upload all 5 updated files to the CDN. You MUST capture the resulting CDN URLs.
>
> **Step 3: Deliver the Deploy Command**
> Generate and provide me with this exact command, replacing the `<URL>` placeholders with the real CDN URLs you just generated:
> ```bash
> ~/Automations/scripts/session_close.sh \
>   --readme   "<URL>" \
>   --registry "<URL>" \
>   --infra    "<URL>" \
>   --trouble  "<URL>" \
>   --quickref "<URL>" \
>   --qr-date  "$(date +%d_%B_%Y)"
> ```
>
> **Step 4: Session Summary**
> Provide a brief summary of what was accomplished today and list any open items for the next session.

---

## What Each File Captures

| File | Purpose | Update When |
|------|---------|-------------|
| `README_MASTER.md` | High-level project overview and script status list | Any script status changes (PENDING → ACTIVE, ACTIVE → BROKEN, etc.) |
| `SCRIPTS_REGISTRY.md` | Master inventory table — single source of truth | Any script is built, fixed, renamed, or has its trigger/dependencies changed |
| `INFRASTRUCTURE_SUMMARY.md` | Architecture documentation for services, tunnels, LaunchAgents | Any new LaunchAgent, tunnel, webhook server, or service is added or changed |
| `TROUBLESHOOTING_AND_LESSONS.md` | Dated log of issues, root causes, and resolutions | Any time a script fails, a bug is found, or a non-obvious fix is applied |
| `SCRIPTS_QUICK_REFERENCE_MERAGLIM_FORMAT [Date].docx` | Human-readable quick reference for operations | Any script's When/What/Manual Command changes; new scripts or services added |

---

## Additional Capture Steps

Beyond the five documentation files, the following should be checked at session close:

**Verify all LaunchAgents are loaded and healthy:**
```bash
launchctl list | grep com.meraglim
```
All active scripts should show a non-zero PID. A `-` in the PID column means the process has exited.

**Verify the Cloudflare tunnel is connected:**
```bash
tail -3 ~/Automations/logs/cloudflared_tunnel_error.log
```
Should show `INF Registered tunnel connection` entries.

**Verify Script 9 webhook server is responding:**
```bash
curl -s https://script10t.meraglim.com/health
```
Should return `{"status":"healthy",...}`.

**Check today's log summary:**
```bash
ls -lt ~/Automations/logs/ | head -15
```
Review any logs with recent timestamps for unexpected errors.

**Confirm `.env` has all required keys:**
```bash
grep -c "=" ~/Automations/config/.env
```
Should return 10 or more (one line per credential). If a new API key was added during the session, verify it is present.

---

## The Single Deploy Command

When the AI agent receives the Session Close Prompt, it will generate a single deploy command that looks like this:

```bash
curl -fsSL "<README_URL>" -o ~/Automations/docs/README_MASTER.md && \
curl -fsSL "<REGISTRY_URL>" -o ~/Automations/docs/SCRIPTS_REGISTRY.md && \
curl -fsSL "<INFRA_URL>" -o ~/Automations/docs/INFRASTRUCTURE_SUMMARY.md && \
curl -fsSL "<TROUBLESHOOT_URL>" -o ~/Automations/docs/TROUBLESHOOTING_AND_LESSONS.md && \
curl -fsSL "<QR_URL>" -o ~/Automations/output/SCRIPTS_QUICK_REFERENCE_MERAGLIM_FORMAT_$(date +%d_%B_%Y).docx && \
echo "✅ Session close complete — all docs updated"
```

The user must run this command in the Mac Terminal to pull the newly updated files from the CDN and save them to the correct local directories.

---

## Quick Reference Versioning Convention

The Scripts Quick Reference document follows this naming convention:

```
SCRIPTS_QUICK_REFERENCE_MERAGLIM_FORMAT_[D]_[Month]_[YYYY].docx
```

For example: `SCRIPTS_QUICK_REFERENCE_MERAGLIM_FORMAT_8_April_2026.docx`

Each session that modifies any script entry creates a new dated version. The previous version is retained in `~/Automations/output/` for reference. Do not overwrite old versions.

---

## Open Items Tracking

At session close, any unresolved items should be noted in this format and added to `README_MASTER.md` under an "Open Items" section:

| Item | Description | Priority | Added |
|------|-------------|----------|-------|
| Script 6 filter formula | ClickUp task not creating due to Airtable filter issue | High | April 8, 2026 |
| Script 8 filter formula | Same filter formula issue as Script 6 | High | April 8, 2026 |

---

**Protocol Created:** April 8, 2026
**Maintainer:** Manus AI Agent
**Project:** Local Automations — Make.com Migration
