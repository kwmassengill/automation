# Script 2 - Quick Reference Guide

## Essential Commands

### Check if Running
\`\`\`bash
launchctl list | grep com.meraglim.script_02_qualification_email
\`\`\`
Expected: \`- 0 com.meraglim.script_02_qualification_email\`

### View Live Logs
\`\`\`bash
tail -f ~/Automations/logs/script_02_airtable_qualification_email.log
\`\`\`

### Stop Script
\`\`\`bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist
\`\`\`

### Start Script
\`\`\`bash
launchctl load ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist
\`\`\`

### Restart Script
\`\`\`bash
launchctl unload ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist && launchctl load ~/Library/LaunchAgents/com.meraglim.script_02_qualification_email.plist
\`\`\`

### Run Manually (One-time)
\`\`\`bash
/usr/bin/python3 ~/Automations/scripts/script_02_airtable_qualification_email_oauth.py
\`\`\`

### Clear State Database (Reset Processed Records)
\`\`\`bash
rm ~/Automations/config/state.db
\`\`\`

### Reset Gmail OAuth Token
\`\`\`bash
rm ~/Automations/config/oauth_token.json
\`\`\`

---

## Testing Workflow

### 1. Create Test Prospect in Airtable
- First Name: "Test"
- Email: your email
- In Automation: checked
- Qualification Status: "New"

### 2. Clear State Database
\`\`\`bash
rm ~/Automations/config/state.db
\`\`\`

### 3. Run Script
\`\`\`bash
/usr/bin/python3 ~/Automations/scripts/script_02_airtable_qualification_email_oauth.py
\`\`\`

### 4. Check Email
- Look for email from kmassengill@meraglim.com
- Verify formatting (Times New Roman, proper line breaks)
- Check subject line includes company name

### 5. Verify Airtable Updates
- Date Sent: timestamp
- Qualification Status: "Qualification Email Sent"
- Deal Phase: "Initial Contact — Awaiting response"
- Deal Phase Date: today's date
- Priority: "Watch — Strategic monitor, no active pursuit"

---

## Troubleshooting Checklist

- [ ] Script running? \`launchctl list | grep com.meraglim.script_02_qualification_email\`
- [ ] Check logs? \`tail -20 ~/Automations/logs/script_02_airtable_qualification_email.log\`
- [ ] Airtable filter correct? Email + In Automation + Status = "New"
- [ ] Gmail OAuth token valid? \`cat ~/Automations/config/oauth_token.json\`
- [ ] State database corrupted? \`rm ~/Automations/config/state.db\`

---

## Key Settings

| Setting | Value | Location |
|---------|-------|----------|
| Frequency | Every 15 minutes (900 seconds) | plist file |
| Max Emails Per Run | 1 | script line 38 |
| Dry Run | False | script line 39 |
| Airtable Base | appoNkgoKHAUXgXV9 | script line 47 |
| Airtable Table | tblxEhVek8ldTQMW1 | script line 48 |

---

## Email Template Customization

To change the email template, edit the \`get_email_template()\` function in:
\`\`\`
~/Automations/scripts/script_02_airtable_qualification_email_oauth.py
\`\`\`

Key variables:
- \`{first_name}\` - Prospect's first name
- \`{fields.get('Company', 'Your Company')}\` - Company name
- Video URL: https://youtu.be/L0WIPiMFtRs
- Font: Times New Roman (change in body style )

---

## Common Issues & Fixes

### "No emails being sent"
1. Check filter: Email exists + In Automation checked + Status = "New"
2. Run manual test: \`/usr/bin/python3 ~/Automations/scripts/script_02_airtable_qualification_email_oauth.py\`
3. Check logs for errors

### "Duplicate emails sent"
1. Clear state: \`rm ~/Automations/config/state.db\`
2. Restart: \`launchctl unload ... && launchctl load ...\`

### "Gmail OAuth error"
1. Delete token: \`rm ~/Automations/config/oauth_token.json\`
2. Run script manually to re-authenticate
3. Follow browser login

### "Script not running"
1. Check status: \`launchctl list | grep com.meraglim.script_02_qualification_email\`
2. Check errors: \`tail -f ~/Automations/logs/script_02_launchagent_error.log\`
3. Restart: \`launchctl unload ... && launchctl load ...\`

---

**Last Updated**: March 23, 2026
