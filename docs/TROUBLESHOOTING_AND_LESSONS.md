# Troubleshooting Guide & Lessons Learned

## The Duplicate Task Crisis (March 21, 2026)

### What Happened

1. **Initial Setup (Day 1):** Created Script 1 (Google Sheets to Airtable sync) and attempted to schedule it using Manus scheduler
2. **Problem Discovered (Day 2):** Hundreds of "Sync Prospects from Google Sheets" tasks were being created in Manus every 5 minutes
3. **Root Cause:** The Manus scheduler was creating a new Manus task every 5 minutes instead of just running a local script
4. **Impact:** Over 100 duplicate tasks accumulated, consuming credits unexpectedly

### Timeline of Discovery

| Time | Event |
|------|-------|
| Day 1 | Manus scheduler configured for Script 1 |
| Day 2 | User noticed 100+ duplicate tasks in Manus queue |
| 14:43 | Realized cron job was removed but tasks still being created |
| 15:30 | Discovered Manus had a "Scheduled" task creating the duplicates |
| 15:32 | Deleted the Manus scheduled task |
| 15:37 | Created macOS LaunchAgent as replacement |
| 15:40+ | Verified no new duplicate tasks being created |

### Solutions Attempted

#### ❌ Attempt 1: Manus Scheduler
- **Result:** Created hundreds of duplicate tasks
- **Lesson:** Never use Manus scheduler for local script execution

#### ❌ Attempt 2: Cron Job
- **Result:** Cron job was monitored by Manus, creating tasks anyway
- **Lesson:** Even removing cron didn't help because Manus had a separate scheduled task

#### ✅ Attempt 3: macOS LaunchAgent
- **Result:** Script runs locally, no Manus tasks created
- **Lesson:** This is the correct approach for macOS automation

### Key Lessons

1. **Never use Manus scheduler for local scripts** — It is designed for Manus tasks, not local execution.
2. **LaunchAgents are the native macOS solution** — They are built-in, free, and reliable.
3. **Always verify the execution method** — Check if tasks are being created in Manus when they should not be.
4. **Monitor logs closely** — The script_01.log showed the script was running correctly locally.
5. **Separate concerns** — Manus is for AI tasks; LaunchAgent is for local automation.

---

## How to Identify Similar Issues

### Warning Signs

- **Unexpected tasks appearing in Manus queue** — Check if there is a scheduled task in Manus.
- **Script running but Manus tasks being created** — Verify the execution method.
- **Duplicate tasks with same name** — Look for a Manus schedule or automation.
- **Charges without visible work** — Check Manus task history.

### Debugging Steps

1. **Check Manus Scheduled Tasks:** Go to Manus dashboard → Filter by "Scheduled" tasks → Look for any active schedules related to your scripts.

2. **Check LaunchAgents:**
   ```bash
   launchctl list | grep com.meraglim
   ```

3. **Check Cron Jobs:**
   ```bash
   crontab -l
   ```

4. **Monitor Script Execution:**
   ```bash
   tail -f ~/Automations/logs/script_01.log
   ```

5. **Check for Manus Tasks:** Go to your Manus "All tasks" view and look for new tasks appearing in real-time.

---

## Technical Details

### Why LaunchAgent is Better Than Cron

| Feature | Cron | LaunchAgent |
|---------|------|-------------|
| Native to macOS | ✗ | ✓ |
| Survives reboots | ✓ | ✓ |
| Easy to manage | ✗ | ✓ |
| Built-in logging | ✗ | ✓ |
| Can run on boot | ✗ | ✓ |
| Manus integration risk | ✓ | ✗ |
| Monitoring tools | Limited | Excellent |

---

## April 8, 2026 — Script 9 Rebuild, Python 3.9 Types, and Cloudflare Tunnel

### Issue 1: Script 9 Polling vs Webhook Architecture

**Symptom:** Script 9 was built to poll Clay's API (`api.clay.com/v1/enrichment/results`), but all requests returned 404 or "deprecated API endpoint."

**Root Cause:** Clay does not have a polling API for enrichment results. The original Make.com scenario was a webhook receiver — Clay pushes data out when enrichment completes. The script was built with the wrong architecture.

**Resolution:** Script 9 was completely rewritten as a Flask HTTP server listening on port 8000. Clay was reconfigured to POST to `https://script10t.meraglim.com/clay-webhook` instead of the old Make.com webhook URL (`https://hook.us2.make.com/gq8f3w0txlu5hp2l38lurh9pn9agkmiv`).

**Rule going forward:** Any script that receives data from an external service (Clay, Make.com, Zapier, etc.) must be a webhook receiver, not a polling script. Check the original Make.com blueprint — if Module 1 is a "Custom Webhook" trigger, the local replacement must be an HTTP server.

---

### Issue 2: Python 3.9 Type Hint Incompatibility

**Symptom:** Script 9 crashed on startup with `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`.

**Root Cause:** The script used the union type hint syntax `dict | None`, which was introduced in Python 3.10. The Mac is running Python 3.9 (the system default on macOS Monterey/Ventura).

**Resolution:** Changed the syntax to `Optional[dict]` from the `typing` module, which is backwards-compatible with Python 3.9.

**Rule going forward:** All scripts must be written for Python 3.9 compatibility. Avoid `X | Y` union type hints; use `Optional[X]` or `Union[X, Y]` from `typing` instead.

---

### Issue 3: LaunchAgent Working Directory and `.env` Loading

**Symptom:** Script 9 reported "Clay API key not configured" even though the key was present in `~/Automations/config/.env`.

**Root Cause:** `shared_utils.py` used a bare `load_dotenv()` call with no path argument. When run by a LaunchAgent, the working directory is the system root, not the script's folder, so Python could not find the `.env` file by relative path.

**Resolution:** Updated `shared_utils.py` to use an explicit absolute path: `load_dotenv("/Users/kevinmassengill/Automations/config/.env")`. This permanently fixes credential loading for all scripts running as LaunchAgents.

**Rule going forward:** Never use bare `load_dotenv()` in any script. Always specify the full absolute path to the `.env` file.

---

### Issue 4: CDN Caching on File Re-Uploads

**Symptom:** After fixing the Python 3.9 type hint and re-uploading the file to the Manus CDN, the `curl` deploy command still downloaded the old broken version.

**Root Cause:** The Manus CDN caches uploaded files. If a file is edited and re-uploaded quickly, the CDN may serve the previously cached version from the old URL.

**Resolution:** Always re-upload to get a fresh CDN URL, then verify the downloaded file contains the expected changes before deploying:
```bash
curl -fsSL "<new_cdn_url>" | grep "expected_text"
```

**Rule going forward:** After any file fix and re-upload, always verify the new CDN URL serves the corrected content before running the deploy command on the Mac.

---

### Issue 5: Cloudflare Tunnel DNS Proxy Status

**Symptom:** `https://script10t.meraglim.com/health` returned empty even though the tunnel was running and the DNS CNAME record existed.

**Root Cause:** The Cloudflare DNS record for `script10t.meraglim.com` had Proxy Status set to "DNS only" (grey cloud). Cloudflare tunnels require the record to be **Proxied** (orange cloud) to route traffic through the tunnel infrastructure.

**Resolution:** In the Cloudflare dashboard (DNS → Records), toggled the `script10t` CNAME record from "DNS only" to "Proxied." The health check responded immediately after the change.

**Rule going forward:** All Cloudflare tunnel CNAME records must be set to **Proxied** (orange cloud). "DNS only" bypasses the tunnel and will not work.

---

---

## April 8, 2026 — GitHub Session Sync, Repo Cleanup, and Workflow Optimization

### Issue 1: Session State Lost Between Tasks (Manus Sandbox Isolation)

**Symptom:** Each new Manus task starts with a completely fresh sandbox. Files updated during a session do not persist to the next task's sandbox automatically. The previous workaround was manually attaching 5 documentation files at the start of every task.

**Root Cause:** Manus sandbox isolation is by design — each task gets a clean environment. The project shared files directory (`/home/ubuntu/projects/`) is read-only and cannot be updated programmatically from inside a task.

**Resolution:** Implemented a GitHub-based session sync system:
1. Created a public GitHub repo at `https://github.com/kwmassengill/automation`
2. `session_close.sh` now auto-commits and pushes `docs/` and `scripts/` to GitHub at every session close
3. The opening prompt includes `curl` commands that pull all 5 docs from raw GitHub URLs into `/tmp/` at session start
4. PAT stored in macOS Keychain — no password prompts
5. `.gitignore` excludes all credentials (`.env`, `google_token.json`, `logs/`)

**Result:** Zero-friction session handoff. No file attachments needed at task start. State is always current in GitHub.

---

### Issue 2: Repository Contained 41 Stale Files

**Symptom:** After the initial push to GitHub, the repo contained `.backup`, `.bak`, `_oauth` duplicate scripts, old variant filenames, per-script README files, and one-time session artifact docs.

**Root Cause:** The `~/Automations/` directory had accumulated files from multiple development sessions without cleanup.

**Resolution:** Audited all 68 files in the repo. Removed 17 stale script files and 24 stale doc files. Moved `requirements.txt` from `docs/` to `scripts/`. Committed and pushed the clean repo. Final state: 19 canonical scripts + 7 core docs.

**Rule going forward:** The canonical script filename for each script number is the one without any suffix (`_oauth`, `_deal`, `_trigger`, `_backup`, `.bak`). When a script is rebuilt or fixed, the canonical file is updated in place — no new filename variants.

---

### Issue 3: README_MASTER.md and SCRIPTS_REGISTRY.md Were Severely Outdated

**Symptom:** The GitHub versions of both files reflected an early-session state — Scripts 2–11 shown as "Pending", incorrect filenames (e.g., `script_05_qualified_7day_followup.py`), and Scripts 6 and 8 still marked `NEEDS FIX` even after they were repaired.

**Root Cause:** The session close protocol in the Scripts 6/8 repair task generated updated docs, but those docs were based on incomplete context (the agent in that task did not have full visibility into the current project state).

**Resolution:** Both files completely rewritten this session to reflect accurate current state: all scripts active, correct canonical filenames, correct infrastructure details, and current open items.

**Rule going forward:** At the start of each session close, the agent must pull the current docs from GitHub and read them before writing updates — not rely solely on the current session's context.

---

### Issue 4: SESSION_CLOSE_PROTOCOL.md Referenced Old Workflow

**Symptom:** The protocol still referenced `SCRIPTS_QUICK_REFERENCE_MERAGLIM_FORMAT_[Date].docx`, the `--quickref` flag, and a curl-based deploy flow instead of the new GitHub-push workflow.

**Resolution:** SESSION_CLOSE_PROTOCOL.md rewritten to reflect the current tested workflow: 5 markdown docs only (no DOCX), `session_close.sh` with `--opening` flag for `STANDARD_OPENING_PROMPT.md`, and explicit note that `session_close.sh` auto-pushes to GitHub.

---

## Contact Information

**If duplicate tasks appear again:**

1. Check Manus "Scheduled" tasks for any active schedules.
2. Delete any Manus scheduled tasks.
3. Verify LaunchAgent is still loaded: `launchctl list | grep com.meraglim`
4. Check logs: `tail -f ~/Automations/logs/scriptXX.log`
5. Contact Manus support if issue persists: https://manus.im/feedback
