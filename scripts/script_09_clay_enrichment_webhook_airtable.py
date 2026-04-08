#!/usr/bin/env python3
"""
Script 09: Clay Enrichment Webhook → Airtable
==============================================
Replaces Make.com Scenario 9.

Architecture:
  Clay (enrichment complete) → POST to Cloudflare Tunnel → This Flask server
  → Search Airtable for matching company → Update record with enriched fields

Clay sends a JSON payload with:
  company_name, website, linkedin_url, industry, city, state

This server:
  1. Receives the POST at /clay-webhook
  2. Searches Airtable table tblxEhVek8ldTQMW1 for a record where
     {Company} = company_name
  3. Updates that record with: Industry, LinkedIn Company URL, State, City
  4. Returns 200 OK so Clay knows the webhook was received

LaunchAgent runs this server persistently on port 5009.
Cloudflare tunnel (script10t) routes external HTTPS traffic to localhost:5009.

Author: Manus AI
Date: 2026-04-08
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from typing import Optional

# ── Third-party imports ──────────────────────────────────────────────────────
try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Flask not installed. Run: pip3 install flask")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip3 install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("python-dotenv not installed. Run: pip3 install python-dotenv")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────────────────────────
SCRIPT_NAME = "script_09_clay_enrichment_webhook_airtable"
PORT = 5009
LOG_DIR = Path("/Users/kevinmassengill/Automations/logs")
ENV_PATH = Path("/Users/kevinmassengill/Automations/config/.env")

# Airtable identifiers (from Blueprint 9)
AIRTABLE_BASE_ID = "appoNkgoKHAUXgXV9"
AIRTABLE_TABLE_ID = "tblxEhVek8ldTQMW1"

# Airtable field IDs (from Blueprint 9 mapper)
FIELD_INDUSTRY          = "fldXdyJeAyuashHvJ"   # Industry
FIELD_LINKEDIN_COMPANY  = "fldfy57JK8nAJctaf"   # LinkedIn Company URL
FIELD_STATE             = "flds0yxdCqd1bEzxY"   # State
FIELD_CITY              = "fldyCGYCIZxdTlrQF"   # City

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"{SCRIPT_NAME}_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(SCRIPT_NAME)

# ── Load credentials ──────────────────────────────────────────────────────────
load_dotenv(dotenv_path=str(ENV_PATH))
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY") or os.getenv("AIRTABLE_TOKEN")

if not AIRTABLE_API_KEY:
    logger.error("AIRTABLE_API_KEY not found in .env — cannot update Airtable records.")
    sys.exit(1)

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
}

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)


# ── Airtable helpers ──────────────────────────────────────────────────────────

def search_airtable_by_company(company_name: str) -> Optional[dict]:
    """
    Search Airtable for a record where {Company} = company_name.
    Returns the first matching record dict, or None.
    """
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    # Escape single quotes in company name for formula
    safe_name = company_name.replace("'", "\\'")
    params = {
        "filterByFormula": f'{{Company}} = "{safe_name}"',
        "maxRecords": 1,
    }
    try:
        resp = requests.get(url, headers=AIRTABLE_HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        if records:
            logger.info(f"Found Airtable record for company '{company_name}': {records[0]['id']}")
            return records[0]
        else:
            logger.warning(f"No Airtable record found for company '{company_name}'")
            return None
    except requests.RequestException as e:
        logger.error(f"Airtable search error for '{company_name}': {e}")
        return None


def update_airtable_record(record_id: str, fields: dict) -> bool:
    """
    PATCH an Airtable record with the given fields dict.
    Returns True on success.
    """
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}/{record_id}"
    payload = {"fields": fields}
    try:
        resp = requests.patch(url, headers=AIRTABLE_HEADERS, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info(f"Updated Airtable record {record_id} with fields: {list(fields.keys())}")
        return True
    except requests.RequestException as e:
        logger.error(f"Airtable update error for record {record_id}: {e}")
        return False


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@app.route("/clay-webhook", methods=["POST"])
def clay_webhook():
    """
    Receives Clay enrichment POST payload and updates Airtable.

    Expected JSON body:
      {
        "company_name": "Acme Corp",
        "website":      "acme.com",
        "linkedin_url": "https://linkedin.com/company/acme",
        "industry":     "Technology",
        "city":         "Atlanta",
        "state":        "GA"
      }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        logger.info(f"Received Clay webhook payload: {json.dumps(data)}")

        company_name = (data.get("company_name") or "").strip()
        if not company_name:
            logger.warning("Payload missing 'company_name' — skipping.")
            return jsonify({"status": "skipped", "reason": "missing company_name"}), 200

        # Step 1: Find the matching Airtable record
        record = search_airtable_by_company(company_name)
        if not record:
            return jsonify({
                "status": "not_found",
                "reason": f"No Airtable record for company '{company_name}'"
            }), 200

        record_id = record["id"]

        # Step 2: Build the fields update (only include non-empty values)
        fields_to_update = {}

        industry = (data.get("industry") or "").strip()
        if industry:
            fields_to_update[FIELD_INDUSTRY] = industry

        linkedin_url = (data.get("linkedin_url") or "").strip()
        if linkedin_url:
            fields_to_update[FIELD_LINKEDIN_COMPANY] = linkedin_url

        state = (data.get("state") or "").strip()
        if state:
            fields_to_update[FIELD_STATE] = state

        city = (data.get("city") or "").strip()
        if city:
            fields_to_update[FIELD_CITY] = city

        if not fields_to_update:
            logger.warning(f"No enrichment fields to update for '{company_name}' — payload had no usable data.")
            return jsonify({"status": "skipped", "reason": "no enrichment fields in payload"}), 200

        # Step 3: Update the Airtable record
        success = update_airtable_record(record_id, fields_to_update)

        if success:
            logger.info(f"✅ Successfully enriched '{company_name}' (record {record_id})")
            return jsonify({
                "status": "success",
                "record_id": record_id,
                "company": company_name,
                "fields_updated": list(fields_to_update.keys()),
            }), 200
        else:
            logger.error(f"Failed to update Airtable record {record_id} for '{company_name}'")
            return jsonify({"status": "error", "reason": "Airtable update failed"}), 500

    except Exception as e:
        logger.exception(f"Unexpected error processing Clay webhook: {e}")
        return jsonify({"status": "error", "reason": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint — useful for monitoring."""
    return jsonify({
        "status": "healthy",
        "script": SCRIPT_NAME,
        "timestamp": datetime.now().isoformat(),
    }), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": SCRIPT_NAME, "endpoints": ["/clay-webhook", "/health"]}), 200


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"Starting {SCRIPT_NAME} webhook server on port {PORT}")
    logger.info(f"Clay should POST enrichment results to: http://localhost:{PORT}/clay-webhook")
    logger.info(f"Via Cloudflare tunnel: https://<your-tunnel-hostname>/clay-webhook")
    app.run(host="0.0.0.0", port=PORT, debug=False)
