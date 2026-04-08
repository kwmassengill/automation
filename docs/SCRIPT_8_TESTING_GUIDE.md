# Script 8: Testing & Validation Guide

**Purpose:** Ensure Script 8 works correctly before deploying to production  
**Estimated Time:** 30-45 minutes  
**Prerequisites:** .env file configured with API keys

---

## Testing Protocol

Follow this 5-step testing protocol to validate Script 8 before production deployment:

### Step 1: API Isolation Tests (5 minutes)

Before running the full script, test each API in isolation to ensure connectivity and authentication.

#### Test Airtable Connection

```bash
# Test Airtable API
curl -H "Authorization: Bearer YOUR_AIRTABLE_API_KEY" \
  "https://api.airtable.com/v0/meta/bases"

# Expected response: List of your bases
# If you get 401: API key is invalid
# If you get 403: API key doesn't have required scopes
```

#### Test ClickUp Connection

```bash
# Test ClickUp API
curl -H "Authorization: pk_YOUR_CLICKUP_API_KEY" \
  "https://api.clickup.com/api/v2/team"

# Expected response: Your team information
# If you get 401: API key is invalid
```

### Step 2: Unit Tests with Mock Data (10 minutes)

Create a test file to verify the filter logic without making API calls.

#### Create `test_script_08.py`

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Import the filter function
from script_08_meeting_scheduled_clickup import should_process_meeting

# Test Case 1: All conditions met (should process)
test_record_1 = {
    "id": "rec_test_001",
    "fields": {
        "Qualification Status": "Meeting Scheduled",
        "Email": "john@company.com",
        "Meeting Date": "2026-03-25",
        "In Automation": True
    }
}
assert should_process_meeting(test_record_1) == True, "Test 1 failed"
print("✓ Test 1 passed: All conditions met")

# Test Case 2: Wrong status (should skip)
test_record_2 = {
    "id": "rec_test_002",
    "fields": {
        "Qualification Status": "Not Qualified",
        "Email": "john@company.com",
        "Meeting Date": "2026-03-25",
        "In Automation": True
    }
}
assert should_process_meeting(test_record_2) == False, "Test 2 failed"
print("✓ Test 2 passed: Wrong status filtered out")

# Test Case 3: Missing email (should skip)
test_record_3 = {
    "id": "rec_test_003",
    "fields": {
        "Qualification Status": "Meeting Scheduled",
        "Email": "",
        "Meeting Date": "2026-03-25",
        "In Automation": True
    }
}
assert should_process_meeting(test_record_3) == False, "Test 3 failed"
print("✓ Test 3 passed: Missing email filtered out")

# Test Case 4: Missing meeting date (should skip)
test_record_4 = {
    "id": "rec_test_004",
    "fields": {
        "Qualification Status": "Meeting Scheduled",
        "Email": "john@company.com",
        "Meeting Date": "",
        "In Automation": True
    }
}
assert should_process_meeting(test_record_4) == False, "Test 4 failed"
print("✓ Test 4 passed: Missing meeting date filtered out")

# Test Case 5: In Automation flag not set (should skip)
test_record_5 = {
    "id": "rec_test_005",
    "fields": {
        "Qualification Status": "Meeting Scheduled",
        "Email": "john@company.com",
        "Meeting Date": "2026-03-25",
        "In Automation": False
    }
}
assert should_process_meeting(test_record_5) == False, "Test 5 failed"
print("✓ Test 5 passed: In Automation flag not set filtered out")

print("\n✅ All unit tests passed!")
```

#### Run the tests

```bash
python3 test_script_08.py
```

**Expected output:**
```
✓ Test 1 passed: All conditions met
✓ Test 2 passed: Wrong status filtered out
✓ Test 3 passed: Missing email filtered out
✓ Test 4 passed: Missing meeting date filtered out
✓ Test 5 passed: In Automation flag not set filtered out

✅ All unit tests passed!
```

### Step 3: Dry Run with Real Data (10 minutes)

Test the full script with real Airtable data without making any API calls.

#### Prepare for dry run

1. Ensure `DRY_RUN=True` in your `.env` file
2. Create at least one test record in Airtable with:
   - `Qualification Status` = "Meeting Scheduled"
   - `Email` = valid email address
   - `Meeting Date` = future date
   - `In Automation` = checked

#### Run the script

```bash
python3 /Users/kevinmassengill/Automations/scripts/script_08_meeting_scheduled_clickup.py
```

#### Check the logs

```bash
tail -50 /Users/kevinmassengill/Automations/logs/script_08_meeting_scheduled_clickup_*.log
```

**Expected log output:**
```
2026-03-24 10:15:30 - script_08_meeting_scheduled_clickup - INFO - Starting script_08_meeting_scheduled_clickup (DRY_RUN=True)
2026-03-24 10:15:31 - script_08_meeting_scheduled_clickup - INFO - Found 1 records with 'Meeting Scheduled' status
2026-03-24 10:15:31 - script_08_meeting_scheduled_clickup - INFO - Processing record rec_xxxxx for john@company.com
2026-03-24 10:15:31 - script_08_meeting_scheduled_clickup - INFO - [DRY RUN] Would create ClickUp task: Company Discover Call - John Doe
2026-03-24 10:15:31 - script_08_meeting_scheduled_clickup - INFO - [DRY RUN] Would update Airtable record rec_xxxxx with: {...}
2026-03-24 10:15:31 - script_08_meeting_scheduled_clickup - INFO - Finished. Processed: 1, Skipped: 0
```

**Verify:**
- ✓ Script finds the test record
- ✓ Record passes all filters
- ✓ Script logs what it WOULD do (not actually doing it)
- ✓ No actual ClickUp tasks created
- ✓ No actual Airtable updates made

### Step 4: Production Test with Real Data (10 minutes)

Now test with actual API calls to ClickUp and Airtable.

#### Prepare for production test

1. Change `DRY_RUN=False` in your `.env` file
2. Keep the same test record from Step 3
3. Note the current state of the test record in Airtable

#### Run the script

```bash
python3 /Users/kevinmassengill/Automations/scripts/script_08_meeting_scheduled_clickup.py
```

#### Verify in ClickUp

1. Go to ClickUp and navigate to the "Upcoming Meetings [Tasks: 1]" list
2. Look for a new task named: `[Company] Discover Call - [Prospect Name]`
3. Verify the task contains:
   - Rich Markdown description with prospect details
   - Pre-call checklist
   - Custom fields populated (EBITDA, Payment Preference, etc.)
   - Due date set to the meeting date

#### Verify in Airtable

1. Go back to the test record in Airtable
2. Verify the following fields were updated:
   - `ClickUp Task ID` = the ID from the ClickUp task
   - `Qualification Status` = "Prep Task Created"
   - `Prep Task Created Date` = today's date

#### Check the logs

```bash
tail -50 /Users/kevinmassengill/Automations/logs/script_08_meeting_scheduled_clickup_*.log
```

**Expected log output:**
```
2026-03-24 10:20:30 - script_08_meeting_scheduled_clickup - INFO - Starting script_08_meeting_scheduled_clickup (DRY_RUN=False)
2026-03-24 10:20:31 - script_08_meeting_scheduled_clickup - INFO - Found 1 records with 'Meeting Scheduled' status
2026-03-24 10:20:31 - script_08_meeting_scheduled_clickup - INFO - Processing record rec_xxxxx for john@company.com
2026-03-24 10:20:32 - script_08_meeting_scheduled_clickup - INFO - Successfully created ClickUp task: clk_xxxxx
2026-03-24 10:20:33 - script_08_meeting_scheduled_clickup - INFO - Successfully updated Airtable record rec_xxxxx
2026-03-24 10:20:33 - script_08_meeting_scheduled_clickup - INFO - Finished. Processed: 1, Skipped: 0
```

### Step 5: LaunchAgent Scheduling Test (5 minutes)

Verify the LaunchAgent loads and runs on schedule.

#### Load the LaunchAgent

```bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script_08_meeting_scheduled_clickup.plist
```

#### Verify it's loaded

```bash
launchctl list | grep script_08
# Should output: 0 com.meraglim.script_08_meeting_scheduled_clickup
```

#### Monitor for first run

```bash
# Watch the logs for the next 15 minutes
tail -f /Users/kevinmassengill/Automations/logs/script_08_meeting_scheduled_clickup_*.log
```

#### Manual trigger for testing

```bash
# Force immediate run (don't wait 15 minutes)
launchctl start com.meraglim.script_08_meeting_scheduled_clickup

# Check logs
tail -20 /Users/kevinmassengill/Automations/logs/script_08_meeting_scheduled_clickup_*.log
```

---

## Validation Checklist

Before marking Script 8 as production-ready, verify all items:

### Functionality Tests
- [ ] Filter logic correctly identifies records with "Meeting Scheduled" status
- [ ] Records without email are filtered out
- [ ] Records without meeting date are filtered out
- [ ] Records without "In Automation" flag are filtered out
- [ ] ClickUp task is created with correct name format
- [ ] ClickUp task description includes all required sections
- [ ] Custom fields are populated correctly
- [ ] Airtable record is updated with ClickUp Task ID
- [ ] Airtable status changes to "Prep Task Created"

### Reliability Tests
- [ ] Script handles API errors gracefully
- [ ] Script logs all actions and errors
- [ ] No duplicate tasks are created on subsequent runs
- [ ] Script completes without unhandled exceptions

### Performance Tests
- [ ] Script completes in under 5 seconds per record
- [ ] No API rate limit errors
- [ ] LaunchAgent runs on 15-minute schedule

### Logging Tests
- [ ] All log messages are clear and actionable
- [ ] Error logs include sufficient context
- [ ] DRY_RUN mode is clearly indicated in logs
- [ ] Logs are written to correct file location

---

## Troubleshooting During Testing

### Issue: "401 Unauthorized" from Airtable
**Solution:** Verify your `AIRTABLE_API_KEY` in the `.env` file is correct and has the required scopes.

### Issue: "404 Not Found" from ClickUp
**Solution:** Verify your `CLICKUP_LIST_ID` is correct. Get it from ClickUp → List → Settings.

### Issue: Script doesn't find any records
**Solution:** Verify you have at least one Airtable record with:
- `Qualification Status` = exactly "Meeting Scheduled" (case-sensitive)
- `Email` = not empty
- `Meeting Date` = not empty
- `In Automation` = checked

### Issue: Task created but Airtable not updated
**Solution:** Check the logs for "Failed to update Airtable record". Verify your `AIRTABLE_API_KEY` has write permissions.

### Issue: LaunchAgent not running
**Solution:** Check the plist syntax:
```bash
plutil -lint ~/Library/LaunchAgents/com.meraglim.script_08_meeting_scheduled_clickup.plist
```

---

## Production Deployment Checklist

Once all tests pass, you're ready for production:

- [ ] All 5 testing steps completed successfully
- [ ] All items in validation checklist verified
- [ ] `DRY_RUN=False` in production `.env` file
- [ ] LaunchAgent loaded and running
- [ ] Logs are being written correctly
- [ ] Team is aware of the automation
- [ ] Backup API keys created
- [ ] Error notification email configured (optional)

---

## Monitoring After Deployment

After deploying to production, monitor these metrics for the first week:

| Metric | Expected | Check |
|--------|----------|-------|
| Records processed per day | 5-20 | `grep "Processed:" ~/Automations/logs/script_08_*.log` |
| Error rate | 0% | `grep "ERROR\|error" ~/Automations/logs/script_08_*.log` |
| Task creation success | 100% | Verify ClickUp tasks created for each Airtable record |
| Airtable update success | 100% | Verify ClickUp Task ID populated in Airtable |
| LaunchAgent execution | Every 15 min | Check logs for regular execution |

---

## Success Criteria

Script 8 is production-ready when:

✅ All 5 testing steps complete successfully  
✅ All validation checklist items verified  
✅ No errors in logs  
✅ ClickUp tasks created with correct data  
✅ Airtable records updated correctly  
✅ LaunchAgent runs on schedule  
✅ Team is trained and aware  

---

**Testing Completed By:** ________________  
**Date:** ________________  
**Status:** ☐ Ready for Production  ☐ Needs Fixes
