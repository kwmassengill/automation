#!/bin/bash
# =============================================================================
# session_close.sh — Meraglim Local Automations
# Downloads updated docs from CDN and pushes to GitHub.
#
# SECURITY NOTE: No credentials are stored in this script.
# Git authentication uses the macOS Keychain credential helper,
# which was configured once with: git config --global credential.helper osxkeychain
#
# Usage:
#   bash ~/Automations/scripts/session_close.sh \
#     --readme    "<CDN_URL>" \
#     --registry  "<CDN_URL>" \
#     --infra     "<CDN_URL>" \
#     --trouble   "<CDN_URL>" \
#     --protocol  "<CDN_URL>" \
#     --qr-date   "$(date '+%Y-%m-%d')"
# =============================================================================

set -euo pipefail

DOCS_DIR="$HOME/Automations/docs"
SCRIPTS_DIR="$HOME/Automations/scripts"
REPO_DIR="$HOME/Automations"

# ── Parse arguments ──────────────────────────────────────────────────────────
README_URL=""
REGISTRY_URL=""
INFRA_URL=""
TROUBLE_URL=""
PROTOCOL_URL=""
QR_DATE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --readme)    README_URL="$2";   shift 2 ;;
    --registry)  REGISTRY_URL="$2"; shift 2 ;;
    --infra)     INFRA_URL="$2";    shift 2 ;;
    --trouble)   TROUBLE_URL="$2";  shift 2 ;;
    --protocol)  PROTOCOL_URL="$2"; shift 2 ;;
    --qr-date)   QR_DATE="$2";      shift 2 ;;
    *)           echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Validate required args ────────────────────────────────────────────────────
for var in README_URL REGISTRY_URL INFRA_URL TROUBLE_URL PROTOCOL_URL; do
  if [[ -z "${!var}" ]]; then
    echo "❌ Missing required argument: --${var//_URL/} (lowercase)"
    exit 1
  fi
done

echo "📥 Downloading updated docs from CDN..."
mkdir -p "$DOCS_DIR"

curl -fsSL "$README_URL"    -o "$DOCS_DIR/README_MASTER.md"            && echo "  ✅ README_MASTER.md"
curl -fsSL "$REGISTRY_URL"  -o "$DOCS_DIR/SCRIPTS_REGISTRY.md"         && echo "  ✅ SCRIPTS_REGISTRY.md"
curl -fsSL "$INFRA_URL"     -o "$DOCS_DIR/INFRASTRUCTURE_SUMMARY.md"   && echo "  ✅ INFRASTRUCTURE_SUMMARY.md"
curl -fsSL "$TROUBLE_URL"   -o "$DOCS_DIR/TROUBLESHOOTING_AND_LESSONS.md" && echo "  ✅ TROUBLESHOOTING_AND_LESSONS.md"
curl -fsSL "$PROTOCOL_URL"  -o "$DOCS_DIR/SESSION_CLOSE_PROTOCOL.md"   && echo "  ✅ SESSION_CLOSE_PROTOCOL.md"

# ── Git push to GitHub ────────────────────────────────────────────────────────
echo ""
echo "🚀 Pushing to GitHub..."

cd "$REPO_DIR"

# Ensure the remote uses HTTPS without credentials embedded in the URL
# Authentication is handled by macOS Keychain (git credential.helper osxkeychain)
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
if echo "$CURRENT_REMOTE" | grep -q "@"; then
  echo "  ⚠️  Remote URL contains embedded credentials — fixing..."
  git remote set-url origin "https://github.com/kwmassengill/automation.git"
  echo "  ✅ Remote URL cleaned (credentials now handled by macOS Keychain)"
fi

git add docs/ scripts/ .gitignore 2>/dev/null || true
git add docs/ scripts/ 2>/dev/null || true

COMMIT_MSG="session close — ${QR_DATE:-$(date '+%Y-%m-%d')}"
if git diff --cached --quiet; then
  echo "  ℹ️  No changes to commit — docs already up to date"
else
  git commit -m "$COMMIT_MSG"
  echo "  ✅ Committed: $COMMIT_MSG"
fi

git push origin main
echo "  ✅ Pushed to https://github.com/kwmassengill/automation"

# ── Health checks ─────────────────────────────────────────────────────────────
echo ""
echo "🔍 Running health checks..."

echo ""
echo "  LaunchAgents:"
launchctl list | grep com.meraglim | awk '{printf "    %s\n", $0}' || echo "    (none found)"

echo ""
echo "  Cloudflare tunnel (last 3 log lines):"
TUNNEL_LOG="$HOME/Automations/logs/cloudflared_tunnel_error.log"
if [[ -f "$TUNNEL_LOG" ]]; then
  tail -3 "$TUNNEL_LOG" | awk '{printf "    %s\n", $0}'
else
  echo "    (log not found)"
fi

echo ""
echo "  Script 9/10T webhook health:"
HEALTH=$(curl -s --max-time 5 https://script10t.meraglim.com/health 2>/dev/null || echo "unreachable")
echo "    $HEALTH"

echo ""
echo "  .env key count:"
ENV_FILE="$HOME/Automations/config/.env"
if [[ -f "$ENV_FILE" ]]; then
  COUNT=$(grep -c "=" "$ENV_FILE" 2>/dev/null || echo "0")
  echo "    $COUNT entries"
else
  echo "    (not found)"
fi

echo ""
echo "  Recent log files:"
ls -lt "$HOME/Automations/logs/" 2>/dev/null | head -8 | awk '{printf "    %s\n", $0}' || echo "    (no logs directory)"

echo ""
echo "✅ Session close complete — $(date '+%Y-%m-%d %H:%M')"
