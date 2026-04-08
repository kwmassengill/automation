# Script 4 Deployment Checklist

## Pre-Deployment Phase

- [ ] Blueprint analyzed and requirements understood
- [ ] Email template reviewed and approved
- [ ] Airtable filter formula tested in Airtable UI
- [ ] Field IDs documented and verified
- [ ] Gmail OAuth credentials configured
- [ ] All required environment variables set in `.env`

## Development Phase

- [x] Python script created with all features
- [x] Gmail OAuth 2.0 integration implemented
- [x] Airtable API integration implemented
- [x] SQLite state tracking implemented
- [x] Email validation implemented
- [x] Comprehensive logging added
- [x] Error handling and safeguards added
- [x] DRY_RUN mode implemented
- [x] MAX_EMAILS_PER_RUN = 1 set
- [x] LaunchAgent plist created
- [x] Documentation created (README, Deployment Checklist)

## Testing Phase

### Manual Testing
- [ ] Test prospect created in Airtable with:
  - First Name: "Test"
  - Email: Your test email
  - Company: "Test Company"
  - In Automation: Checked
  - Qualification Status: "Not Qualified"

- [ ] Clear state database:
  ```bash
  rm ~/Automations/config/state.db
  ```

- [ ] Run script with DRY_RUN = True:
  ```bash
  /usr/bin/python3 ~/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py
  ```

- [ ] Verify logs show what would happen without errors

- [ ] Set DRY_RUN = False in script

- [ ] Run script manually again:
  ```bash
  /usr/bin/python3 ~/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py
  ```

### Verification
- [ ] Email received at test address
- [ ] Email formatting looks correct (no HTML tags visible)
- [ ] Email subject contains company name
- [ ] Email body contains personalized first name
- [ ] Airtable record updated with:
  - [ ] Date Sent field populated
  - [ ] Qualification Status changed to "Declined Email Sent"
- [ ] State database created
- [ ] Run script again to verify no duplicate emails sent
- [ ] Check logs for any errors or warnings

## Deployment Phase

### File Placement
- [ ] Copy script to scripts directory:
  ```bash
  cp script_04_not_qualified_polite_decline_oauth.py ~/Automations/scripts/
  chmod +x ~/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py
  ```

- [ ] Copy plist to LaunchAgents directory:
  ```bash
  cp com.meraglim.script_04_not_qualified_polite_decline.plist ~/Library/LaunchAgents/
  ```

### LaunchAgent Loading
- [ ] Load LaunchAgent:
  ```bash
  launchctl load ~/Library/LaunchAgents/com.meraglim.script_04_not_qualified_polite_decline.plist
  ```

- [ ] Verify LaunchAgent is loaded:
  ```bash
  launchctl list | grep com.meraglim.script_04
  ```
  Expected output: Should show a line with the plist name and a process ID

- [ ] Check for any load errors:
  ```bash
  launchctl list | grep -A 5 com.meraglim.script_04
  ```

### Initial Verification
- [ ] Wait 15 minutes for first automatic execution
- [ ] Check logs for successful execution:
  ```bash
  tail -20 ~/Automations/logs/script_04_not_qualified_polite_decline_*.log
  ```

- [ ] Verify no errors in error log:
  ```bash
  cat ~/Automations/logs/script_04_launchagent_error.log
  ```

- [ ] Verify LaunchAgent is still running:
  ```bash
  launchctl list | grep com.meraglim.script_04
  ```

## Post-Deployment Phase

### Monitoring (First 24 Hours)
- [ ] Monitor logs every 2-3 hours
- [ ] Verify emails are being sent to prospects
- [ ] Check Airtable for record updates
- [ ] Monitor for any error patterns

### Ongoing Monitoring (First Week)
- [ ] Check logs daily
- [ ] Verify email delivery (check Gmail sent folder)
- [ ] Verify Airtable updates are correct
- [ ] Adjust email template if needed
- [ ] Document any issues or improvements

### Production Handoff
- [ ] Script is stable and running correctly
- [ ] No errors in logs
- [ ] All prospects receiving emails as expected
- [ ] Airtable records updating correctly
- [ ] Ready for next script deployment

## Rollback Plan

If something goes wrong:

1. **Unload LaunchAgent:**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.meraglim.script_04_not_qualified_polite_decline.plist
   ```

2. **Clear state database (if needed):**
   ```bash
   rm ~/Automations/config/state.db
   ```

3. **Review logs for errors:**
   ```bash
   tail -100 ~/Automations/logs/script_04_*.log
   ```

4. **Fix the issue and redeploy**

## Important Notes

- **MAX_EMAILS_PER_RUN = 1**: This is intentional and mandatory. It ensures only one email is sent per execution, preventing accidental mass emails.
- **DRY_RUN Mode**: Always test with DRY_RUN = True first before setting to False.
- **State Tracking**: The SQLite database prevents duplicate emails to the same prospect.
- **Gmail OAuth**: The first run may require browser authentication. This is normal.
- **LaunchAgent Interval**: Currently set to 900 seconds (15 minutes). Can be adjusted in the plist file if needed.

## Support & Troubleshooting

### Script Not Running
1. Check if LaunchAgent is loaded: `launchctl list | grep com.meraglim.script_04`
2. Check error logs: `tail -50 ~/Automations/logs/script_04_launchagent_error.log`
3. Reload LaunchAgent: `launchctl unload ... && launchctl load ...`

### Gmail Authentication Issues
1. Delete the token file: `rm ~/Automations/config/oauth_token.json`
2. Run the script manually to trigger OAuth flow
3. Follow the browser authentication process

### Airtable API Errors
1. Verify API key in `.env` file
2. Verify Base ID and Table ID are correct
3. Test filter formula in Airtable UI first

### Email Formatting Issues
1. Check the email template in the script
2. Verify HTML tags are correct (use `<p>` tags, not `<br>`)
3. Test email format in actual Gmail before production

---

**Created by:** Manus AI  
**Date:** March 23, 2026  
**Status:** Ready for Deployment
