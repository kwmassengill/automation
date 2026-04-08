# Standard Opening Prompt — Meraglim Automation Stack

Paste the text below (between the triple dashes) at the start of every new Manus task in the "Local Automations – Make.com Migration" project. No file attachments needed.

---

You are continuing work on the Meraglim Local Automation Stack. Before doing anything else, run the following command to pull the latest session state from GitHub:

```
curl -fsSL https://raw.githubusercontent.com/kwmassengill/automation/main/docs/README_MASTER.md -o /tmp/README_MASTER.md && \
curl -fsSL https://raw.githubusercontent.com/kwmassengill/automation/main/docs/SCRIPTS_REGISTRY.md -o /tmp/SCRIPTS_REGISTRY.md && \
curl -fsSL https://raw.githubusercontent.com/kwmassengill/automation/main/docs/INFRASTRUCTURE_SUMMARY.md -o /tmp/INFRASTRUCTURE_SUMMARY.md && \
curl -fsSL https://raw.githubusercontent.com/kwmassengill/automation/main/docs/TROUBLESHOOTING_AND_LESSONS.md -o /tmp/TROUBLESHOOTING_AND_LESSONS.md && \
curl -fsSL https://raw.githubusercontent.com/kwmassengill/automation/main/docs/SESSION_CLOSE_PROTOCOL.md -o /tmp/SESSION_CLOSE_PROTOCOL.md && \
echo "✅ Docs pulled from GitHub"
```

Read all five files before creating any plan or taking any action. Then proceed with the task below.

**Platform context:**
- macOS Apple Silicon, username: kevinmassengill
- Python: /usr/bin/python3 (3.9)
- Homebrew: /opt/homebrew/bin/
- LaunchAgents: ~/Library/LaunchAgents/com.meraglim.*
- All scripts use google_token.json (not oauth_token.json)
- GitHub repo: https://github.com/kwmassengill/automation (private)

**Task:**

[PASTE YOUR TASK DESCRIPTION HERE]

---
