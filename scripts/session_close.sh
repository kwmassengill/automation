#!/bin/bash
# session_close.sh — Meraglim Automation Session Close
# Deploys updated docs from CDN and pushes everything to GitHub

set -e

AUTOMATIONS_DIR="$HOME/Automations"
DOCS_DIR="$AUTOMATIONS_DIR/docs"
SCRIPTS_DIR="$AUTOMATIONS_DIR/scripts"

# ── Parse flags ──────────────────────────────────────────────────────────────
README_URL=""
REGISTRY_URL=""
INFRA_URL=""
TROUBLE_URL=""
QUICKREF_URL=""
PROTOCOL_URL=""
OPENING_URL=""
QR_DATE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --readme)      README_URL="$2";   shift 2 ;;
    --registry)    REGISTRY_URL="$2"; shift 2 ;;
    --infra)       INFRA_URL="$2";    shift 2 ;;
    --trouble)     TROUBLE_URL="$2";  shift 2 ;;
    --quickref)    QUICKREF_URL="$2"; shift 2 ;;
    --protocol)    PROTOCOL_URL="$2"; shift 2 ;;
    --opening)     OPENING_URL="$2";  shift 2 ;;
    --qr-date)     QR_DATE="$2";      shift 2 ;;
    *) echo "Unknown flag: $1"; shift ;;
  esac
done

# ── Download updated docs from CDN ───────────────────────────────────────────
echo "📥 Downloading updated docs..."

[[ -n "$README_URL" ]]   && curl -fsSL "$README_URL"   -o "$DOCS_DIR/README_MASTER.md"           && echo "  ✅ README_MASTER.md"
[[ -n "$REGISTRY_URL" ]] && curl -fsSL "$REGISTRY_URL" -o "$DOCS_DIR/SCRIPTS_REGISTRY.md"        && echo "  ✅ SCRIPTS_REGISTRY.md"
[[ -n "$INFRA_URL" ]]    && curl -fsSL "$INFRA_URL"    -o "$DOCS_DIR/INFRASTRUCTURE_SUMMARY.md"  && echo "  ✅ INFRASTRUCTURE_SUMMARY.md"
[[ -n "$TROUBLE_URL" ]]  && curl -fsSL "$TROUBLE_URL"  -o "$DOCS_DIR/TROUBLESHOOTING_AND_LESSONS.md" && echo "  ✅ TROUBLESHOOTING_AND_LESSONS.md"
[[ -n "$QUICKREF_URL" ]] && curl -fsSL "$QUICKREF_URL" -o "$DOCS_DIR/SCRIPTS_QUICK_REFERENCE.md" && echo "  ✅ SCRIPTS_QUICK_REFERENCE.md"
[[ -n "$PROTOCOL_URL" ]] && curl -fsSL "$PROTOCOL_URL" -o "$DOCS_DIR/SESSION_CLOSE_PROTOCOL.md"  && echo "  ✅ SESSION_CLOSE_PROTOCOL.md"
[[ -n "$OPENING_URL" ]]  && curl -fsSL "$OPENING_URL"  -o "$DOCS_DIR/STANDARD_OPENING_PROMPT.md" && echo "  ✅ STANDARD_OPENING_PROMPT.md"

# ── Push to GitHub ────────────────────────────────────────────────────────────
echo ""
echo "📤 Pushing to GitHub..."

cd "$AUTOMATIONS_DIR"

# Initialize git repo if not already done
if [[ ! -d ".git" ]]; then
  git init
  git remote add origin https://kwmassengill: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@github.com/kwmassengill/automation.git
  git branch -M main
  echo "  ✅ Git repo initialized"
fi

# Stage all docs and scripts
git add docs/ scripts/

COMMIT_MSG="session-close $(date '+%Y-%m-%d %H:%M')"
if [[ -n "$QR_DATE" ]]; then
  COMMIT_MSG="session-close $QR_DATE"
fi

git commit -m "$COMMIT_MSG" 2>/dev/null || echo "  ℹ️  Nothing new to commit"
git push origin main 2>/dev/null && echo "  ✅ Pushed to GitHub" || echo "  ⚠️  Push failed — check credentials"

# ── Health check ─────────────────────────────────────────────────────────────
echo ""
echo "🏥 Running health checks..."
python3 "$SCRIPTS_DIR/script_00_daily_log_analysis_native.py" --quick 2>/dev/null || echo "  ℹ️  Health check skipped (script not available)"

echo ""
echo "✅ Session close complete."
