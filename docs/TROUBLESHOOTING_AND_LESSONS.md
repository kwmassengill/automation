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

## Contact Information

**If duplicate tasks appear again:**

1. Check Manus "Scheduled" tasks for any active schedules.
2. Delete any Manus scheduled tasks.
3. Verify LaunchAgent is still loaded: `launchctl list | grep com.meraglim`
4. Check logs: `tail -f ~/Automations/logs/scriptXX.log`
5. Contact Manus support if issue persists: https://manus.im/feedback
