#!/bin/bash

# ============================================================================
# Cron Job Setup Script for Meraglim Automations
# ============================================================================
# This script sets up all cron jobs for the automation scripts.
# Run this script ONCE to install all cron jobs.
#
# Usage: bash /Users/kevinmassengill/Automations/setup_cron_jobs.sh
# ============================================================================

set -e

AUTOMATIONS_DIR="/Users/kevinmassengill/Automations"
SCRIPTS_DIR="$AUTOMATIONS_DIR/scripts"
LOGS_DIR="$AUTOMATIONS_DIR/logs"
PYTHON_BIN="/usr/bin/python3"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Meraglim Automations - Cron Setup${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if Python is installed
if ! command -v $PYTHON_BIN &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 not found at $PYTHON_BIN${NC}"
    echo "Please install Python 3 or update the PYTHON_BIN variable in this script."
    exit 1
fi

echo -e "${YELLOW}Python found: $($PYTHON_BIN --version)${NC}\n"

# Check if directories exist
if [ ! -d "$SCRIPTS_DIR" ]; then
    echo -e "${RED}ERROR: Scripts directory not found: $SCRIPTS_DIR${NC}"
    exit 1
fi

if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${YELLOW}Creating logs directory...${NC}"
    mkdir -p "$LOGS_DIR"
fi

# Create a temporary crontab file
CRON_FILE="/tmp/meraglim_crontab_$$.txt"

# Get existing crontab (if any)
crontab -l > "$CRON_FILE" 2>/dev/null || true

# Define cron jobs
# Format: minute hour day month day_of_week command

# Script 1: Google Sheets to Airtable (every 5 minutes)
echo "*/5 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_01_google_sheets_to_airtable.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 2: Airtable New Prospect → Send Qualification Email (every 5 minutes)
echo "*/5 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_02_airtable_qualification_email.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 3: Qualified Prospect - Calendar Invite (every 5 minutes)
echo "*/5 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_03_qualified_prospect_calendar_invite.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 4: Not Qualified - Polite Decline (every 5 minutes)
echo "*/5 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_04_not_qualified_polite_decline.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 5: No Response - 7 Day Follow Up (every 10 minutes)
echo "*/10 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_05_no_response_7day_followup.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 6: Qualified Prospect → ClickUp Deal Pipeline (every 5 minutes)
echo "*/5 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_06_qualified_prospect_clickup_deal.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 7: Gmail Reply → AI Qualification (every 5 minutes)
echo "*/5 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_07_gmail_reply_ai_qualification.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 8: Meeting Scheduled → ClickUp Prep Task (every 5 minutes)
echo "*/5 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_08_meeting_scheduled_clickup_prep.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script 9: Clay Enrichment Webhook → Airtable (every 10 minutes)
echo "*/10 * * * * cd $SCRIPTS_DIR && $PYTHON_BIN script_09_clay_enrichment_webhook_airtable.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script MHC-10T: Meeting Intelligence Trigger (every 5 minutes, 8am-6pm weekdays)
echo "*/5 8-18 * * 1-5 cd $SCRIPTS_DIR && $PYTHON_BIN script_mhc10t_meeting_intelligence_trigger.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script MHC-10: Meeting Intelligence Sync (every 10 minutes, 8am-6pm weekdays)
echo "*/10 8-18 * * 1-5 cd $SCRIPTS_DIR && $PYTHON_BIN script_mhc10_meeting_intelligence_sync.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Script MHC-11: Post-Meeting Intelligence Sync (every 5 minutes, 8am-6pm weekdays)
echo "*/5 8-18 * * 1-5 cd $SCRIPTS_DIR && $PYTHON_BIN script_mhc11_post_meeting_intelligence_sync.py >> $LOGS_DIR/cron.log 2>&1" >> "$CRON_FILE"

# Remove duplicates (in case this script is run multiple times)
sort "$CRON_FILE" | uniq > "$CRON_FILE.tmp"
mv "$CRON_FILE.tmp" "$CRON_FILE"

# Install the crontab
crontab "$CRON_FILE"

# Clean up
rm "$CRON_FILE"

echo -e "${GREEN}✓ Cron jobs installed successfully!${NC}\n"

# Display the installed cron jobs
echo -e "${YELLOW}Installed cron jobs:${NC}"
crontab -l | grep -v "^#" | grep -v "^$" | grep "meraglim\|script_" || echo "No cron jobs found"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo "Your automation scripts are now scheduled to run automatically."
echo ""
echo "To view cron logs:"
echo "  tail -f $LOGS_DIR/cron.log"
echo ""
echo "To edit cron jobs:"
echo "  crontab -e"
echo ""
echo "To remove all cron jobs:"
echo "  crontab -r"
echo ""
