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

1. **Never use Manus scheduler for local scripts** - It's designed for Manus tasks, not local execution
2. **LaunchAgents are the native macOS solution** - They're built-in, free, and reliable
3. **Always verify the execution method** - Check if tasks are being created in Manus when they shouldn't be
4. **Monitor logs closely** - The script_01.log showed the script was running correctly locally
5. **Separate concerns** - Manus is for AI tasks; LaunchAgent is for local automation

## How to Identify Similar Issues

### Warning Signs

- **Unexpected tasks appearing in Manus queue** - Check if there's a scheduled task in Manus
- **Script running but Manus tasks being created** - Verify the execution method
- **Duplicate tasks with same name** - Look for a Manus schedule or automation
- **Charges without visible work** - Check Manus task history

### Debugging Steps

1. **Check Manus Scheduled Tasks:**
   - Go to Manus dashboard
   - Filter by "Scheduled" tasks
   - Look for any active schedules related to your scripts

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

5. **Check for Manus Tasks:**
   - Go to your Manus "All tasks" view
   - Look for new tasks appearing in real-time

## Prevention Strategies

### For Future Scripts

1. **Always use LaunchAgent** for local macOS scripts
2. **Never use Manus scheduler** for local execution
3. **Test script manually first** before scheduling
4. **Monitor logs** for the first 24 hours after deployment
5. **Check Manus task queue** to ensure no unexpected tasks are created

### Best Practices

1. **One LaunchAgent per script** - Separate plist files for each script
2. **Consistent naming** - Use `com.meraglim.scriptXX` format
3. **Comprehensive logging** - Always log to file for debugging
4. **Error notifications** - Include email alerts on failure (in script)
5. **State tracking** - Prevent duplicate processing with state database

## Support Communication

### What We Told Manus Support

**Issue:** Manus scheduler created hundreds of duplicate tasks, consuming credits

**Request:** 
- Batch delete duplicate "Sync Prospects from Google Sheets" tasks
- Review charges from the duplicate tasks
- Consider credit adjustment

**Status:** Awaiting response from support team

### Follow-up Actions

- [ ] Monitor Manus support response
- [ ] Confirm if credits will be adjusted
- [ ] Document final resolution
- [ ] Update this guide with outcome

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

### LaunchAgent Plist Structure

```xml
<key>Label</key>              <!-- Unique identifier -->
<key>ProgramArguments</key>   <!-- Command to execute -->
<key>StartInterval</key>      <!-- Seconds between runs -->
<key>StandardOutPath</key>    <!-- Stdout log file -->
<key>StandardErrorPath</key>  <!-- Stderr log file -->
<key>RunAtLoad</key>          <!-- Auto-start on boot -->
<key>KeepAlive</key>          <!-- Restart if crashes -->
```

## Going Forward

### For Each New Script

1. **Create the Python script** with error handling and logging
2. **Test it manually** to ensure it works
3. **Create a LaunchAgent plist** file
4. **Load the LaunchAgent** with `launchctl load`
5. **Monitor logs** for 24 hours
6. **Verify no Manus tasks** are being created
7. **Document the script** in README

### Script Deployment Checklist

- [ ] Script created and tested manually
- [ ] Script has comprehensive error handling
- [ ] Script has logging to file
- [ ] LaunchAgent plist created
- [ ] LaunchAgent loaded with `launchctl load`
- [ ] LaunchAgent status verified with `launchctl list`
- [ ] Logs monitored for 24 hours
- [ ] No unexpected Manus tasks created
- [ ] Script documented in README
- [ ] Interval and timing documented

## Contact Information

**If duplicate tasks appear again:**

1. Check Manus "Scheduled" tasks for any active schedules
2. Delete any Manus scheduled tasks
3. Verify LaunchAgent is still loaded: `launchctl list | grep com.meraglim`
4. Check logs: `tail -f ~/Automations/logs/scriptXX.log`
5. Contact Manus support if issue persists

**Manus Support:** https://manus.im/feedback

## Scripts 6 & 8 Duplicate Task Creation (April 8, 2026)

### What Happened

**Issue:** Scripts 6 and 8 were creating duplicate ClickUp tasks on every run.
**Symptoms:**
- Multiple identical tasks appearing in ClickUp for the same prospect/meeting.
- Logs showing the script processing the same records repeatedly.
- Filter formulas returning records that had already been processed.

### Root Cause

Both scripts were missing deduplication filters in their Airtable queries. They were using Make.com syntax (`TRUE()`, `FALSE()`) instead of Airtable's native syntax (`1`, `0`) for boolean/checkbox fields.

### Resolution

1. **Script 6:** Added `{ClickUp Task Created} != 1` to the filter formula.
   - *Before:* `AND({Qualification Status} = "Meeting Invite Sent", {In Automation} != BLANK())`
   - *After:* `AND({Qualification Status} = "Meeting Invite Sent", {In Automation} != BLANK(), {ClickUp Task Created} != 1)`
2. **Script 8:** Added `{ClickUp Task Created} != 1` to the filter formula.
   - *Before:* `{Qualification Status} = 'Meeting Scheduled'`
   - *After:* `AND({Qualification Status} = 'Meeting Scheduled', {ClickUp Task Created} != 1)`

### Lesson Learned

When converting Make.com blueprints to Python scripts, always use **native Airtable filter formula syntax**:
- Use `1` and `0` for boolean/checkbox fields instead of `TRUE()` and `FALSE()`.
- Use `BLANK()` for empty field checks.
- Always verify field names exist in your Airtable base (e.g., `{ClickUp Task Created}` instead of `{Prep Task Created}`).
