# Meraglim Holdings — Infrastructure Summary

**Last Updated:** April 8, 2026

---

## Platform

| Component | Value |
|-----------|-------|
| Machine | Apple Silicon MacBook Pro |
| Username | kevinmassengill |
| Python | /usr/bin/python3 (3.9) — system default |
| Homebrew | /opt/homebrew/bin/ (Apple Silicon — NOT /usr/local/bin/) |
| LaunchAgents directory | ~/Library/LaunchAgents/ |
| Scripts directory | ~/Automations/scripts/ |
| Docs directory | ~/Automations/docs/ |
| Config directory | ~/Automations/config/ |
| Logs directory | ~/Automations/logs/ |

---

## Active Services

### Persistent Background Services (always show PID in `launchctl list`)

| Service | LaunchAgent Plist | Port | Public URL | Notes |
|---------|------------------|------|------------|-------|
| Cloudflare Tunnel | `com.meraglim.cloudflared-tunnel` | — | — | Binary: `/opt/homebrew/bin/cloudflared`; 4 connections to ATL edge nodes (atl01/atl06/atl11/atl15) |
| Script 9 Clay Webhook | `com.meraglim.script09-clay-webhook` | 8000 | `https://script10t.meraglim.com/clay-webhook` | Flask HTTP server; receives Clay enrichment POSTs |
| Script 10T Trigger | `com.meraglim.script10t` | 8000 | `https://script10t.meraglim.com` | Meeting intelligence trigger; `/health` endpoint |

### Scheduled Scripts (no PID between runs — normal)

| Script | LaunchAgent | Schedule |
|--------|------------|---------|
| Script 0 | `com.meraglim.script00` | 6 AM daily |
| Script 1 | `com.meraglim.script01` | Every 5 min |
| Script 2 | `com.meraglim.script02` | Every 15 min |
| Script 3 | `com.meraglim.script03` | LaunchAgent |
| Script 4 | `com.meraglim.script04` | Every 15 min |
| Script 5 | `com.meraglim.script05` | Every 15 min |
| Script 6 | `com.meraglim.script06` | LaunchAgent |
| Script 7 | `com.meraglim.script07` | Every 5 min |
| Script 8 | `com.meraglim.script08` | LaunchAgent |
| Script 11 | `com.meraglim.script11-post-meeting-intelligence` | Every 5 min | **NEW — April 8, 2026** |

---

## Cloudflare Tunnel

- **Tunnel name:** `script10t`
- **Public domain:** `script10t.meraglim.com`
- **DNS record type:** CNAME, **Proxied** (orange cloud — required; "DNS only" will not work)
- **Routes to:** `localhost:8000` on the Mac
- **LaunchAgent:** `com.meraglim.cloudflared-tunnel.plist`
- **Binary path:** `/opt/homebrew/bin/cloudflared` (Apple Silicon)
- **Logs:** `~/Automations/logs/cloudflared_tunnel_error.log`
- **Health check:** `curl -s https://script10t.meraglim.com/health`

---

## Credentials & Configuration

- **`.env` location:** `~/Automations/config/.env`
- **`.env` entry count:** 34 keys (added ANTHROPIC_API_KEY on April 8, 2026)
- **Loading method:** Explicit absolute path in `shared_utils.py` — `load_dotenv("/Users/kevinmassengill/Automations/config/.env")`
- **Google OAuth token:** `~/Automations/config/google_token.json` (all scripts use this; never `oauth_token.json`)
- **Key APIs:** Airtable, Gmail (OAuth), Google Calendar, ClickUp, Claude (`claude-sonnet-4-20250514`), Clay (`CLAY_API_KEY=9d1f10e2b7bf089a41ad`), Anthropic

---

## GitHub Session Sync

- **Repository:** https://github.com/kwmassengill/automation (public)
- **PAT:** Stored in macOS Keychain (`git credential-osxkeychain`)
- **Auto-push:** `session_close.sh` commits and pushes `docs/` and `scripts/` to `main` at every session close
- **Auto-pull:** Opening prompt `curl`s all 5 docs from raw GitHub URLs into `/tmp/` at session start
- **`.gitignore` excludes:** `config/.env`, `config/google_token.json`, `config/credentials.json`, `logs/`, `*.log`

---

## Session Handoff Architecture

```
Session Close:
  Agent updates 5 docs → uploads to CDN → provides session_close.sh command
  User runs command in Terminal:
    → docs downloaded from CDN to ~/Automations/docs/
    → git commit + push to GitHub

Session Open (next task):
  User pastes opening prompt
  Agent runs curl commands:
    → 5 docs pulled from raw.githubusercontent.com into /tmp/
    → Agent reads all 5 files before creating any plan
```

---

## Health Check Commands

```bash
# All LaunchAgents
launchctl list | grep com.meraglim

# Cloudflare tunnel log
tail -3 ~/Automations/logs/cloudflared_tunnel_error.log

# Script 9 / Script 10T webhook health
curl -s https://script10t.meraglim.com/health

# .env key count (should be 34)
grep -c "=" ~/Automations/config/.env

# Recent log activity
ls -lt ~/Automations/logs/ | head -15

# Script 11 recent logs
tail -20 ~/Automations/logs/script_11.log
```

---

**Maintained By:** Manus AI Agent  
**Project:** Local Automations — Make.com Migration
