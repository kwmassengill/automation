## Claude Code Session Close

At the end of every Claude Code session, complete these steps in order:

**1. Update any docs that changed this session:**
- README_MASTER.md - update script status table if any status changed
- SCRIPTS_REGISTRY.md - update any script touched this session
- TROUBLESHOOTING_AND_LESSONS.md - append a dated entry for any issue encountered and resolved
- AGENTS.md - append fix notes under the relevant script entry

**2. Run the following from terminal:**

cd ~/Automations
git add docs/ scripts/
git commit -m "session close - [brief description]"
git push

**3. Confirm the push succeeded.** Session is not closed until GitHub reflects the latest state.

---

## Legacy Close Protocol (Manus - Archived)

The prior workflow using CDN upload and session_close.sh is no longer the primary method. It remains available as a fallback if Claude Code is unavailable. The session_close.sh script remains in ~/Automations/scripts/.

## What Each File Captures

| File | Purpose | Update When |
|------|---------|-------------|
| `README_MASTER.md` | High-level project overview and script status table | Any script status changes; infrastructure changes |
| `SCRIPTS_REGISTRY.md` | Master inventory — single source of truth for all scripts | Any script built, fixed, renamed, or has trigger/dependencies changed |
| `INFRASTRUCTURE_SUMMARY.md` | Architecture documentation for services, tunnels, LaunchAgents | Any new LaunchAgent, tunnel, webhook server, or service added or changed |
| `TROUBLESHOOTING_AND_LESSONS.md` | Dated log of issues, root causes, and resolutions | Any time a script fails, a bug is found, or a non-obvious fix is applied |
| `SESSION_CLOSE_PROTOCOL.md` | This file — the close workflow itself | Only when the close workflow changes |

---

## What session_close.sh Does

When you run the `session_close.sh` command on your Mac, it:

1. Downloads all updated docs from CDN to `~/Automations/docs/`
2. Runs `git add docs/ scripts/` in `~/Automations/`
3. Commits with a timestamped message
4. Pushes to `https://github.com/kwmassengill/automation` (main branch)

The PAT is stored in macOS Keychain — no password prompt. The push is fully automatic.

---

## Additional Health Checks at Session Close

```bash
# All LaunchAgents
launchctl list | grep com.meraglim

# Cloudflare tunnel
tail -3 ~/Automations/logs/cloudflared_tunnel_error.log

# Script 9 / 10T webhook health
curl -s https://script10t.meraglim.com/health

# .env key count (should be 34)
grep -c "=" ~/Automations/config/.env

# Recent log activity
ls -lt ~/Automations/logs/ | head -15
```

---

## Open Items Tracking

At session close, unresolved items should be noted in `README_MASTER.md` under the "Open Items" section in this format:

| Item | Priority | Added |
|------|----------|-------|
| Description of open item | High / Medium / Low | Date |

---

**Protocol Created:** April 8, 2026  
**Last Updated:** April 8, 2026  
**Maintainer:** Manus AI Agent  
**Project:** Local Automations — Make.com Migration
