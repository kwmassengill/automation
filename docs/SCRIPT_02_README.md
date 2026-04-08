# Script 2: Airtable Qualification Email Automation

## Overview

**Script 2** monitors the Airtable Prospects table for new prospects and automatically sends personalized qualification emails via Gmail OAuth. It runs every 15 minutes via macOS LaunchAgent.

**Status**: ✅ Production Ready

---

## What It Does

1. **Monitors Airtable** for prospects matching three criteria:
   - Email field is not blank
   - In Automation = TRUE (checked)
   - Qualification Status = "New"

2. **Sends Qualification Email** via Gmail OAuth with:
   - Personalized greeting (First Name)
   - Company-specific subject line
   - 5-minute video link
   - Two qualification questions
   - Professional signature (Times New Roman font)

3. **Updates Airtable** with:
   - Date Sent (timestamp)
   - Qualification Status → "Qualification Email Sent"
   - Deal Phase → "Initial Contact — Awaiting response"
   - Deal Phase Date → current date
   - Priority → "Watch — Strategic monitor, no active pursuit"

4. **Prevents Duplicates** via SQLite state tracking database

5. **Logs Everything** to ~/Automations/logs/script_02_airtable_qualification_email.log

---

## Configuration

### Airtable
- **Base ID**: appoNkgoKHAUXgXV9
- **Table ID**: tblxEhVek8ldTQMW1
- **Filter Formula**: `AND(NOT({Email} = BLANK()), {In Automation} = TRUE(), {Qualification Status} = 'New')`

### Field IDs
| Field Name | Field ID |
|-----------|----------|
| Email | (standard field) |
| In Automation | (standard field) |
| Qualification Status | (standard field) |
| Date Sent | fldI2tIVJyDy1Cymi |
| Qualification Status (update) | fldgCH6CyIsNUCkV8 |
| Deal Phase | fld07a0yFNwo92lTs |
| Deal Phase Date | fldNZDQaLsGJoQQhn |
| Priority | fld5E4Nud5bAg0hXb |

### Gmail OAuth
- **Method**: Google OAuth 2.0 (not SMTP)
- **Credentials File**: ~/Automations/config/oauth_credentials.json
- **Token File**: ~/Automations/config/oauth_token.json
- **Scope**: gmail.send

### Safeguards
- **DRY_RUN**: False (set to True to test without sending)
- **MAX_EMAILS_PER_RUN**: 1 (prevents mass mailings)
- **Email Validation**: Regex check for valid format
- **State Tracking**: SQLite database at ~/Automations/config/state.db

---

## Files

| File | Purpose |
|------|---------|
| ~/Automations/scripts/script_02_airtable_qualification_email_oauth.py | Main script |
| ~/Automations/config/oauth_credentials.json | Gmail OAuth credentials |
| ~/Automations/config/oauth_token.json | Gmail OAuth token (auto-generated) |
| ~/Automations/config/state.db | SQLite database tracking processed records |
| ~/Automations/logs/script_02_airtable_qualification_email.log | Execution log |
| ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist | LaunchAgent configuration |

---

## LaunchAgent Setup

### Start the Service
\`\`\`bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist
\`\`\`

### Check Status
\`\`\`bash
launchctl list | grep com.meraglim.script_02_qualification_email
\`\`\`

Expected output: \`- 0 com.meraglim.script_02_qualification_email\`

### Stop the Service
\`\`\`bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist
\`\`\`

### Restart the Service
\`\`\`bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist
launchctl load ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist
\`\`\`

### View Logs
\`\`\`bash
# Main execution log
tail -f ~/Automations/logs/script_02_airtable_qualification_email.log

# LaunchAgent output
tail -f ~/Automations/logs/script_02_launchagent.log

# LaunchAgent errors
tail -f ~/Automations/logs/script_02_launchagent_error.log
\`\`\`

---

## Manual Testing

### Test with Dry Run (No Emails Sent)
1. Edit the script and set \`DRY_RUN = True\`
2. Run: \`/usr/bin/python3 ~/Automations/scripts/script_02_airtable_qualification_email_oauth.py\`
3. Check logs to verify it would send emails
4. Set \`DRY_RUN = False\` when ready

### Test with Real Email
1. Create a test prospect in Airtable with:
   - Email: your test email
   - In Automation: checked
   - Qualification Status: "New"
2. Clear state database: \`rm ~/Automations/config/state.db\`
3. Run script: \`/usr/bin/python3 ~/Automations/scripts/script_02_airtable_qualification_email_oauth.py\`
4. Check your email for the qualification email
5. Verify Airtable record was updated

### Reset a Prospect
To resend an email to a prospect:
1. In Airtable, set Qualification Status back to "New"
2. Clear state database: \`rm ~/Automations/config/state.db\`
3. Run script again

---

## Email Template

### Subject Line
\`\`\`
Two Quick Questions About [Company Name] Before We Meet
\`\`\`

### Body
- Personalized greeting with first name
- Explanation of purpose
- Link to 5-minute video (YouTube)
- Two qualification questions about EBITDA and payout structure
- Professional closing
- Signature with name, title, company, and email

### Font
Times New Roman, 14px

---

## Troubleshooting

### Script Not Running
1. Check LaunchAgent status: \`launchctl list | grep com.meraglim.script_02_qualification_email\`
2. Check error logs: \`tail -f ~/Automations/logs/script_02_launchagent_error.log\`
3. Verify plist file exists: \`ls -la ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist\`

### No Emails Being Sent
1. Check if prospects match filter criteria (Email, In Automation, Status = "New")
2. Check logs: \`tail -f ~/Automations/logs/script_02_airtable_qualification_email.log\`
3. Verify Gmail OAuth token is valid: \`cat ~/Automations/config/oauth_token.json\`
4. Run manual test with dry run enabled

### Duplicate Emails Sent
1. State database may be corrupted
2. Clear it: \`rm ~/Automations/config/state.db\`
3. Restart script: \`launchctl unload ... && launchctl load ...\`

### Gmail OAuth Token Expired
1. Delete token file: \`rm ~/Automations/config/oauth_token.json\`
2. Run script manually to re-authenticate
3. Follow the browser login flow

---

## Key Lessons Learned

### 1. Always Test Before Production
- **Issue**: First email to Josh Davis had incorrect filter (missing status check)
- **Solution**: Always test with a test prospect first
- **Protocol**: Create test prospect → verify email format → check Airtable updates → then deploy

### 2. Email Formatting in Gmail
- **Issue**: HTML \`  
\` tags were rendering as plain text
- **Solution**: Use separate \`<p>\` tags with \`margin: 0; padding: 0;\` for each line
- **Best Practice**: Wrap signature in individual \`<p>\` tags for proper line breaks

### 3. Safeguards Against Mass Mailings
- **MAX_EMAILS_PER_RUN = 1**: Only sends one email per execution
- **DRY_RUN mode**: Test without actually sending
- **Email validation**: Check format before sending
- **State tracking**: SQLite database prevents duplicates

### 4. Filter Formula Syntax
- **Issue**: Field names with special characters need proper escaping
- **Solution**: Use \`AND(NOT({Email} = BLANK()), {In Automation} = TRUE(), {Qualification Status} = 'New')\`
- **Note**: Three conditions must ALL be true (Email exists AND In Automation AND Status = New)

### 5. LaunchAgent vs Cron
- **LaunchAgent**: macOS native scheduler (preferred for Mac)
- **StartInterval**: 900 seconds = 15 minutes
- **RunAtLoad**: true = starts automatically on login
- **Logs**: StandardOutPath and StandardErrorPath capture all output

---

## Monitoring

### Daily Checks
1. Check logs for errors: \`tail -20 ~/Automations/logs/script_02_airtable_qualification_email.log\`
2. Verify LaunchAgent is running: \`launchctl list | grep com.meraglim.script_02_qualification_email\`
3. Check Airtable for updated records

### Weekly Review
1. Count emails sent (check logs)
2. Review any errors or failures
3. Verify Airtable updates are correct

### Monthly Maintenance
1. Archive old logs
2. Review and update email template if needed
3. Check Gmail OAuth token expiration

---

## Future Enhancements

- [ ] Add email scheduling (send at specific times)
- [ ] Add A/B testing for email templates
- [ ] Add reply tracking
- [ ] Add follow-up email sequences
- [ ] Add Slack notifications on errors
- [ ] Add email open tracking

---

## Contact & Support

For questions or issues, check:
1. Logs: ~/Automations/logs/script_02_airtable_qualification_email.log
2. LaunchAgent status: \`launchctl list | grep com.meraglim.script_02_qualification_email\`
3. Airtable filter formula in script

---

**Last Updated**: March 23, 2026
**Status**: Production Ready
**Running**: Every 15 minutes via LaunchAgent
