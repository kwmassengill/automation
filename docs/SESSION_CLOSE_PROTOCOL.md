# Session Close Protocol

This document outlines the standard operating procedure for closing a Manus AI session on the Make.com migration project.

## Prerequisites

Before initiating the session close protocol, ensure:
1. All code changes have been tested and verified.
2. Any new LaunchAgents have been loaded and confirmed running.
3. Logs have been checked for errors.

## Step 1: Update Documentation Files

The AI agent must read and update the following 5 files in the Manus project shared directory to reflect the work completed during the session:

1. **`README_MASTER.md`**
   - Update the script status table (e.g., change from ⏳ Pending to ✅ Active).
   - Update the current state summary and version history.
2. **`SCRIPTS_REGISTRY.md`**
   - Update the status, notes, and known issues for any scripts touched.
3. **`INFRASTRUCTURE_SUMMARY.md`**
   - Update if any services, ports, tunnels, or LaunchAgents changed.
4. **`TROUBLESHOOTING_AND_LESSONS.md`**
   - Append a new dated entry summarizing any issues encountered and their resolutions.
5. **`SCRIPTS_QUICK_REFERENCE_MERAGLIM_FORMAT_[Date].docx`**
   - Update script entries and save as a new dated version (if applicable).

## Step 2: Upload to CDN

The AI agent must use the `manus-upload-file` tool to upload all updated documentation files to the CDN. The resulting CDN URLs MUST be captured for the next step.

## Step 3: Deliver the Deploy Command

The AI agent must generate and provide the user with the exact bash command to execute the local `session_close.sh` script, substituting the real CDN URLs captured in Step 2.

**Format:**
```bash
bash ~/Automations/scripts/session_close.sh \
  --readme    "[README_MASTER.md CDN URL]" \
  --registry  "[SCRIPTS_REGISTRY.md CDN URL]" \
  --infra     "[INFRASTRUCTURE_SUMMARY.md CDN URL]" \
  --trouble   "[TROUBLESHOOTING_AND_LESSONS.md CDN URL]" \
  --protocol  "[SESSION_CLOSE_PROTOCOL.md CDN URL]" \
  --qr-date   "$(date '+%Y-%m-%d')"
```

## Step 4: Session Summary

The AI agent must provide a brief summary of what was accomplished during the session and list any open items for the next session.

---
**Last Updated:** 2026-04-08
