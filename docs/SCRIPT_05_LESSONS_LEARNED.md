# Script 5: Lessons Learned & Troubleshooting Guide

## Implementation Summary

**Script Name:** No Response - 7 Day Follow Up  
**Status:** ✅ Production Ready  
**Last Updated:** March 24, 2026  
**Execution Frequency:** Every 15 minutes via LaunchAgent  

## Key Implementation Decisions

### 1. Gmail OAuth 2.0 vs. SMTP

**Decision:** Use Gmail OAuth 2.0 instead of basic SMTP authentication.

**Rationale:**
- More secure and modern authentication method
- Avoids storing plaintext passwords
- Integrates seamlessly with Google's security model
- Supports token refresh for long-running automations

**Lessons Learned:**
- OAuth tokens can expire and need refresh logic
- The `run_local_server()` method requires a browser, which doesn't work in headless environments (like the sandbox)
- For production on a Mac, the browser authentication happens automatically on first run
- Store the token file (`oauth_token.json`) securely and back it up

### 2. Path Handling: Sandbox vs. Mac

**Problem Encountered:**
The script was hardcoded with sandbox paths (`/home/ubuntu/Automations/config/`) which failed on the Mac (`/Users/kevinmassengill/Automations/config/`).

**Solution Implemented:**
Use `os.path.expanduser("~/Automations/config/")` to make paths portable across systems.

```python
config_env_path = Path(os.path.expanduser("~/Automations/config/.env"))
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", os.path.expanduser("~/Automations/config")))
```

**Lessons Learned:**
- Always use `os.path.expanduser()` for home directory paths
- Test scripts on both sandbox and target machine before deployment
- Document expected directory structure clearly

### 3. Airtable Field IDs Extraction

**Process:**
1. Extracted field IDs from the Make.com Blueprint 5 JSON
2. Verified against Airtable metadata API
3. Discovered that some assumed field IDs were incorrect (e.g., `fldInAutomation` didn't exist; correct ID is `fldArNm1cnJ1zaO8O`)

**Correct Field IDs:**
| Field Name | Field ID |
|---|---|
| First Name | fld6jEciITAhhMj7w |
| Company | fld9QhGE9uzOOEjSg |
| Email | fldBg1qqf4RM1RCyu |
| Qualification Status | fldgCH6CyIsNUCkV8 |
| Date Sent | fldI2tIVJyDy1Cymi |
| In Automation | fldArNm1cnJ1zaO8O |
| Days Since Email | flde4VDrWEJBNevfM |
| Deal Phase | fld07a0yFNwo92lTs |
| Deal Phase Date | fldNZDQaLsGJoQQhn |

**Lessons Learned:**
- Never assume field IDs from documentation; always verify via Airtable metadata API
- Use the metadata API to get authoritative field information
- Document all field IDs in a central location for future reference

### 4. Filter Formula Implementation

**Formula Used:**
```
AND(
  {Qualification Status} = 'Qualification Email Sent',
  NOT({Email} = BLANK()),
  {In Automation} = TRUE(),
  NOT({Date Sent} = BLANK()),
  {Days Since Email} >= 7
)
```

**Critical Components:**
1. **Qualification Status check** - Ensures only prospects at the right stage are processed
2. **Email validation** - Prevents errors when sending to blank emails
3. **In Automation flag** - Safety mechanism to exclude prospects manually
4. **Date Sent validation** - Ensures the initial email was actually sent
5. **Days Since Email >= 7** - Relies on Airtable's calculated field

**Lessons Learned:**
- The `Days Since Email` field must be a calculated field in Airtable using: `IF({Date Sent}, DATETIME_DIFF(NOW(), {Date Sent}, 'days'), 0)`
- Without this field, the filter won't work correctly
- Test the filter formula in Airtable directly before implementing in the script

### 5. Airtable Record Updates

**Fields Updated on Each Follow-Up:**
1. **Qualification Status** → "No Response - Followed Up"
2. **Date Sent** → Current UTC timestamp (ISO format)
3. **Deal Phase** → "Passed — Did not proceed (preserve for reference)"
4. **Deal Phase Date** → Today's date (YYYY-MM-DD format)

**Date Format Handling:**
- **Timestamps** (Date Sent): Use UTC ISO format with "Z" suffix: `2026-03-24T17:21:24.174369Z`
- **Dates** (Deal Phase Date): Use YYYY-MM-DD format: `2026-03-24`

**Lessons Learned:**
- Airtable's date and datetime fields have different format requirements
- Always use UTC for timestamps to avoid timezone issues
- Test date updates in Airtable before deploying to production

### 6. Email Template Design

**Template Characteristics:**
- **Format:** HTML with inline styles
- **Font:** Times New Roman (professional, readable)
- **Structure:** Multiple `<p>` tags with consistent margin spacing
- **Call-to-Action:** Button-style link to YouTube video
- **Personalization:** First name and company name dynamically inserted

**Lessons Learned:**
- Use inline CSS styles instead of external stylesheets for email reliability
- Test email rendering in Gmail, Outlook, and other clients
- Keep emails short and scannable
- Include a clear call-to-action
- Always include sender information (name, title, company, email)

### 7. State Management & Duplicate Prevention

**Implementation:**
Uses SQLite database to track processed records and prevent duplicate follow-ups.

**State Key Format:**
```
script_05_no_response_7_day_followup_{record_id}_followup
```

**Lessons Learned:**
- State tracking prevents accidental duplicate emails
- SQLite is lightweight and doesn't require external dependencies
- Always check state before sending emails
- Update state only after successful Airtable update (not just email send)

### 8. Safeguard Implementation

**Safeguards in Place:**
1. **DRY_RUN mode** - Set to `True` by default; change to `False` only for production
2. **MAX_EMAILS_PER_RUN = 1** - Prevents mass operations in a single run
3. **Comprehensive logging** - Every action is logged for audit trail
4. **Error handling** - Graceful error handling with detailed error messages

**Lessons Learned:**
- Always default to safe mode (DRY_RUN = True)
- Limit batch operations to prevent accidental mass actions
- Log everything for debugging and compliance
- Use try-catch blocks with specific error messages

## Troubleshooting Guide

### Problem: "OAuth credentials file not found"

**Cause:** Script is looking for `oauth_credentials.json` in the wrong location.

**Solution:**
1. Verify the file exists: `ls -la ~/Automations/config/oauth_credentials.json`
2. Check that the path in the script uses `os.path.expanduser("~/Automations/config/")`
3. Ensure the file contains valid JSON from your Google Cloud project

### Problem: "Email sent successfully" but no email received

**Cause:** Email might be in spam folder or OAuth token is invalid.

**Solution:**
1. Check Gmail spam folder
2. Verify OAuth token is valid: `cat ~/Automations/config/oauth_token.json`
3. If token expired, delete it and run the script again to re-authenticate
4. Check Gmail logs for delivery errors

### Problem: Script finds prospects but doesn't update Airtable

**Cause:** Airtable API error or incorrect field IDs.

**Solution:**
1. Check logs for specific Airtable error: `tail -50 ~/Automations/logs/script_05_no_response_7_day_followup.log`
2. Verify field IDs are correct: `python3 -c "import requests; ..."`
3. Test Airtable API manually with curl
4. Ensure Airtable API key has write permissions

### Problem: Script runs but finds 0 prospects

**Cause:** Filter formula is too restrictive or no prospects meet criteria.

**Solution:**
1. Check that test prospects have:
   - Qualification Status = "Qualification Email Sent"
   - Email field is not blank
   - In Automation = True
   - Date Sent is not blank and is >= 7 days old
2. Test the filter formula directly in Airtable
3. Check that `Days Since Email` field is calculating correctly
4. Verify the formula: `IF({Date Sent}, DATETIME_DIFF(NOW(), {Date Sent}, 'days'), 0)`

### Problem: LaunchAgent not running

**Cause:** Plist file not loaded or has syntax errors.

**Solution:**
1. Check if loaded: `launchctl list | grep com.meraglim.script05`
2. Load manually: `launchctl load ~/Library/LaunchAgents/com.meraglim.script05_no_response_7day_followup.plist`
3. Check for errors: `launchctl error <error_code>`
4. Verify plist syntax: `plutil -lint ~/Library/LaunchAgents/com.meraglim.script05_no_response_7day_followup.plist`

### Problem: Script runs but crashes with Python version warning

**Cause:** Python 3.9 is end-of-life; Google libraries recommend Python 3.10+.

**Solution:**
1. This is a warning, not an error; the script still works
2. To fix, upgrade Python: `brew install python@3.11`
3. Update shebang in script to use new Python version
4. Update LaunchAgent plist to point to new Python path

## Performance Considerations

### Execution Time
- **Typical run:** 2-5 seconds per prospect
- **Network latency:** Airtable API calls add ~1-2 seconds per operation
- **Gmail send:** ~1 second per email

### Resource Usage
- **Memory:** ~50-100 MB
- **CPU:** Minimal (mostly I/O bound)
- **Disk:** Logs grow ~5-10 KB per run

### Optimization Tips
- Run every 15 minutes (current schedule) to avoid overwhelming the API
- Consider increasing `MAX_EMAILS_PER_RUN` only if you have high volume
- Monitor log file size and implement rotation if needed

## Security Considerations

### OAuth Token Storage
- **Location:** `~/Automations/config/oauth_token.json`
- **Permissions:** Should be readable only by the user (600)
- **Backup:** Include in encrypted backup of Automations directory
- **Rotation:** Tokens refresh automatically; no manual rotation needed

### API Keys
- **Airtable Key:** Stored in `.env` file
- **Permissions:** Should have read/write access to Prospects table only
- **Rotation:** Consider rotating quarterly
- **Backup:** Keep secure copy in password manager

### Logging
- **Log Location:** `~/Automations/logs/`
- **Sensitive Data:** Logs do NOT contain API keys or email content
- **Retention:** Keep logs for 30 days for debugging
- **Cleanup:** Implement log rotation to prevent disk space issues

## Future Enhancements

### Potential Improvements
1. **Multi-prospect batching** - Increase `MAX_EMAILS_PER_RUN` for higher volume
2. **Custom email templates** - Load templates from files instead of hardcoding
3. **A/B testing** - Send different email variants to different prospects
4. **Response tracking** - Monitor email open rates and click-throughs
5. **Retry logic** - Automatically retry failed sends
6. **Slack notifications** - Send summary to Slack instead of email
7. **Database analytics** - Track follow-up success rates over time

### Technical Debt
1. Extract email template to separate file
2. Implement email template versioning
3. Add unit tests for Airtable interactions
4. Implement circuit breaker for API failures
5. Add metrics/monitoring dashboard

## Deployment Checklist

Before deploying Script 5 to production:

- [ ] Test script with DRY_RUN = True
- [ ] Create test prospects and verify email sends correctly
- [ ] Verify all 4 Airtable fields update correctly
- [ ] Check log files for errors
- [ ] Verify OAuth token is valid and stored securely
- [ ] Confirm .env file has correct paths for Mac
- [ ] Set DRY_RUN = False in production script
- [ ] Copy plist to LaunchAgents folder
- [ ] Load LaunchAgent: `launchctl load ~/Library/LaunchAgents/com.meraglim.script05_no_response_7day_followup.plist`
- [ ] Verify LaunchAgent is running: `launchctl list | grep com.meraglim.script05`
- [ ] Monitor logs for 24 hours to ensure stability
- [ ] Document any custom configurations or modifications

## Contact & Support

For issues or questions about Script 5:
1. Check the logs: `tail -f ~/Automations/logs/script_05_no_response_7_day_followup.log`
2. Review this troubleshooting guide
3. Check the SCRIPT_05_README.md for configuration details
4. Consult the SCRIPT_05_QUICK_REFERENCE.md for common commands
