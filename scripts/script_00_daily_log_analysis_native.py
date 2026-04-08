#!/usr/bin/env python3
"""
Daily Log Analysis Script - NATIVE MAC VERSION
Runs directly on Mac via LaunchAgent at 6 AM CST daily
Analyzes all 11 automation scripts' logs and sends HTML report
to KMassengill@Meraglim.com using Gmail API OAuth

Supports two log timestamp formats:
  - Standard:  2026-04-08 07:31:50 - script_XX - INFO - message
  - Comma-sep: 2026-04-08 09:36:45,316 - INFO - message  (Script 7)
"""

import os
import sys
import glob
import re
import base64
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Google API libraries not installed.")
    print("Run: pip3 install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Configuration - Native Mac paths
AUTOMATIONS_DIR = os.path.expanduser("~/Automations")
LOGS_DIR = os.path.join(AUTOMATIONS_DIR, "logs")
GOOGLE_TOKEN_FILE = os.path.join(AUTOMATIONS_DIR, "config", "google_token.json")
LOGO_FILE = os.path.join(AUTOMATIONS_DIR, "config", "meraglim_logo.jpg")
LOCK_FILE = os.path.join(AUTOMATIONS_DIR, "logs", ".daily_analysis_lock")
RECIPIENT_EMAIL = "KMassengill@Meraglim.com"

SCRIPT_NAMES = {
    "script_01": ("Script 1", "Google Sheets → Airtable"),
    "script_02": ("Script 2", "New Prospect → Qualification Email"),
    "script_03": ("Script 3", "Qualified Prospect → Calendar Invite"),
    "script_04": ("Script 4", "Not Qualified → Polite Decline"),
    "script_05": ("Script 5", "No Response → 7-Day Follow-Up"),
    "script_06": ("Script 6", "Meeting Invite → ClickUp Deal Pipeline"),
    "script_07": ("Script 7", "Gmail Reply → AI Qualification"),
    "script_08": ("Script 8", "Meeting Scheduled → Pre-Meeting Trigger"),
    "script_09": ("Script 9", "Clay Enrichment → Airtable"),
    "script_10": ("Script 10", "Pre-Meeting Intelligence Driver"),
    "script_mhc11": ("Script 11", "Post-Meeting Intelligence Sync")
}


def acquire_lock():
    """Prevent duplicate runs within 5 minutes."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                lock_time = float(f.read().strip())
                elapsed = time.time() - lock_time
                if elapsed < 300:
                    print(f"[SKIP] Another instance ran {elapsed:.0f}s ago. Preventing duplicate.")
                    return False
        except Exception:
            pass
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
    with open(LOCK_FILE, 'w') as f:
        f.write(str(time.time()))
    return True


def release_lock():
    try:
        os.remove(LOCK_FILE)
    except Exception:
        pass


class LogAnalyzer:
    def __init__(self):
        self.results = {}
        self.all_errors = []
        self.summary = {}

    def analyze_all_logs(self):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting log analysis...")
        print(f"Logs directory: {LOGS_DIR}")
        os.makedirs(LOGS_DIR, exist_ok=True)

        for script_key, (script_num, script_name) in SCRIPT_NAMES.items():
            self.analyze_script_logs(script_key, script_num, script_name)

        self.generate_summary()

    def analyze_script_logs(self, script_key, script_num, script_name):
        log_pattern = os.path.join(LOGS_DIR, f"{script_key}*.log")
        log_files = sorted(glob.glob(log_pattern), reverse=True)

        result = {
            "num": script_num,
            "name": script_name,
            "log_files_found": len(log_files),
            "latest_log": None,
            "last_execution": None,
            "status": "NO LOGS",
            "error_count": 0,
            "warning_count": 0,
            "success_count": 0,
            "recent_errors": []
        }

        if log_files:
            latest_log = log_files[0]
            result["latest_log"] = os.path.basename(latest_log)
            mod_time = os.path.getmtime(latest_log)
            result["last_execution"] = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')

            try:
                with open(latest_log, 'r', errors='replace') as f:
                    content = f.read()

                # ----------------------------------------------------------------
                # Timestamp patterns — support BOTH log formats:
                #   Standard:   2026-04-08 07:31:50 - script_XX - INFO - ...
                #   Comma-sep:  2026-04-08 09:36:45,316 - INFO - ...
                #
                # The key regex anchors on ^YYYY-MM-DD and allows an optional
                # comma+milliseconds after the time component.
                # ----------------------------------------------------------------

                # Extract date portion from either format
                # Group 1 = date string (YYYY-MM-DD)
                ts_pat = re.compile(r'^(\d{4}-\d{2}-\d{2})')
                cutoff_str = datetime.now().strftime('%Y-%m-%d')

                # ERROR: line starts with a timestamp AND contains ERROR level
                # Handles both:
                #   "2026-04-08 07:31:50 - script_XX - ERROR - ..."
                #   "2026-04-08 09:36:45,316 - ERROR - ..."
                error_pat = re.compile(
                    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]?\d*\s*[-–]\s*(?:\S+\s*[-–]\s*)?ERROR'
                )

                # WARNING: same dual-format support
                warn_pat = re.compile(
                    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]?\d*\s*[-–]\s*(?:\S+\s*[-–]\s*)?WARN'
                )

                # SUCCESS / INFO indicators — match any timestamped INFO line or
                # known success keywords
                success_pat = re.compile(
                    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]?\d*\s*[-–]\s*(?:\S+\s*[-–]\s*)?INFO'
                    r'|SUCCESS|COMPLETED|completed successfully|Starting|Created|Processed|Skipped',
                    re.IGNORECASE
                )

                for line in content.split('\n'):
                    # Only analyze lines from today
                    ts_match = ts_pat.match(line)
                    if ts_match:
                        if ts_match.group(1) < cutoff_str:
                            continue  # Skip old log entries
                    else:
                        continue  # Skip lines without a timestamp (Traceback continuations, etc.)

                    if error_pat.match(line):
                        result["error_count"] += 1
                        if len(result["recent_errors"]) < 3:
                            result["recent_errors"].append(line.strip()[:120])
                    elif warn_pat.match(line):
                        result["warning_count"] += 1
                    elif success_pat.match(line):
                        result["success_count"] += 1

                if result["error_count"] > 0:
                    result["status"] = "ERRORS"
                    self.all_errors.append(f"{script_num} - {script_name}: {result['error_count']} errors")
                elif result["warning_count"] > 0:
                    result["status"] = "WARNINGS"
                elif result["success_count"] > 0:
                    result["status"] = "HEALTHY"
                else:
                    result["status"] = "NO ACTIVITY"

            except Exception as e:
                result["status"] = "READ ERROR"
                self.all_errors.append(f"{script_num} - {script_name}: Could not read log - {e}")

        self.results[script_key] = result

    def generate_summary(self):
        self.summary = {
            "total": len(self.results),
            "healthy": sum(1 for r in self.results.values() if r["status"] == "HEALTHY"),
            "warnings": sum(1 for r in self.results.values() if r["status"] == "WARNINGS"),
            "errors": sum(1 for r in self.results.values() if r["status"] == "ERRORS"),
            "no_logs": sum(1 for r in self.results.values() if r["status"] in ("NO LOGS", "NO ACTIVITY")),
            "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def generate_html_report(self):
        logo_html = ""
        if os.path.exists(LOGO_FILE):
            logo_html = '<img src="cid:meraglim_logo" style="max-width:160px;height:auto;margin-bottom:15px;">'

        status_icons = {
            "HEALTHY": ("✅ HEALTHY", "#28a745"),
            "WARNINGS": ("⚠️ WARNINGS", "#e6a817"),
            "ERRORS": ("❌ ERRORS", "#dc3545"),
            "NO LOGS": ("📭 NO LOGS", "#6c757d"),
            "NO ACTIVITY": ("📭 NO ACTIVITY", "#6c757d"),
            "READ ERROR": ("❌ READ ERROR", "#dc3545"),
        }

        rows_html = ""
        for result in self.results.values():
            icon_text, color = status_icons.get(result["status"], ("❓ UNKNOWN", "#999"))
            errors_html = ""
            if result["recent_errors"]:
                items = "".join(f"<li style='font-size:11px;color:#555;'>{e}</li>" for e in result["recent_errors"])
                errors_html = f"<ul style='margin:4px 0 0 16px;padding:0;'>{items}</ul>"

            rows_html += f"""
            <tr>
              <td style="padding:10px 12px;border-bottom:1px solid #eee;">
                <strong>{result['num']} - {result['name']}</strong><br>
                <span style="font-size:11px;color:#888;">Last Run: {result['last_execution'] or 'Never'}</span>
                {errors_html}
              </td>
              <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap;">
                <span style="color:{color};font-weight:bold;">{icon_text}</span><br>
                <span style="font-size:11px;color:#888;">Errors: {result['error_count']} | Warnings: {result['warning_count']}</span>
              </td>
            </tr>"""

        issues_html = ""
        if self.all_errors:
            items = "".join(f"<li>{e}</li>" for e in self.all_errors)
            issues_html = f"""
            <div style="background:#fff3cd;border-left:4px solid #e6a817;padding:12px 16px;margin:20px 0;border-radius:4px;">
              <strong>⚠️ Issues Requiring Attention:</strong>
              <ul style="margin:8px 0 0 16px;padding:0;">{items}</ul>
            </div>"""

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;color:#1A1A1A;max-width:700px;margin:0 auto;padding:20px;">
  <div style="background:#1A1A1A;color:white;padding:24px;text-align:center;border-radius:6px 6px 0 0;">
    {logo_html}
    <h1 style="margin:0;font-size:20px;">Meraglim Automation Scripts</h1>
    <p style="margin:6px 0 0;font-size:14px;color:#ccc;">Daily Health Report — {self.summary['analysis_time']}</p>
  </div>

  <div style="background:#f8f8f8;border-left:4px solid #D4AF37;padding:14px 18px;margin:20px 0;border-radius:0 4px 4px 0;">
    <h2 style="margin:0 0 8px;font-size:16px;">📊 Summary</h2>
    <p style="margin:0;">
      <strong>Total Scripts:</strong> {self.summary['total']}&nbsp;&nbsp;|&nbsp;&nbsp;
      <span style="color:#28a745;font-weight:bold;">✅ Healthy: {self.summary['healthy']}</span>&nbsp;&nbsp;|&nbsp;&nbsp;
      <span style="color:#e6a817;font-weight:bold;">⚠️ Warnings: {self.summary['warnings']}</span>&nbsp;&nbsp;|&nbsp;&nbsp;
      <span style="color:#dc3545;font-weight:bold;">❌ Errors: {self.summary['errors']}</span>&nbsp;&nbsp;|&nbsp;&nbsp;
      <span style="color:#6c757d;font-weight:bold;">📭 No Logs: {self.summary['no_logs']}</span>
    </p>
  </div>

  {issues_html}

  <h2 style="font-size:16px;margin:20px 0 8px;">📋 Script Status</h2>
  <table style="width:100%;border-collapse:collapse;border:1px solid #ddd;border-radius:4px;">
    {rows_html}
  </table>

  <div style="text-align:center;color:#aaa;font-size:11px;margin-top:30px;padding-top:16px;border-top:1px solid #eee;">
    Meraglim Automation System &nbsp;·&nbsp; Next report: Tomorrow at 6:00 AM CST
  </div>
</body>
</html>"""

    def send_via_gmail_api(self):
        if not os.path.exists(GOOGLE_TOKEN_FILE):
            print(f"❌ Token file not found: {GOOGLE_TOKEN_FILE}")
            return False
        try:
            creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE)
            if creds.expired:
                creds.refresh(Request())

            service = build("gmail", "v1", credentials=creds)

            msg = MIMEMultipart("related")
            msg_alt = MIMEMultipart("alternative")
            msg.attach(msg_alt)
            msg["Subject"] = f"Meraglim Automation Health Report — {datetime.now().strftime('%Y-%m-%d')}"
            msg["From"] = "me"
            msg["To"] = RECIPIENT_EMAIL

            msg_alt.attach(MIMEText(self.generate_html_report(), "html"))

            if os.path.exists(LOGO_FILE):
                with open(LOGO_FILE, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<meraglim_logo>')
                    img.add_header('Content-Disposition', 'inline', filename='meraglim_logo.jpg')
                    msg.attach(img)

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
            print(f"✅ Report sent to {RECIPIENT_EMAIL} via Gmail API")
            return True
        except Exception as e:
            print(f"❌ Gmail API error: {e}")
            return False


def main():
    if not acquire_lock():
        sys.exit(0)
    try:
        analyzer = LogAnalyzer()
        analyzer.analyze_all_logs()

        # Console output
        print("\n" + "=" * 60)
        print("MERAGLIM AUTOMATION SCRIPTS - DAILY HEALTH REPORT")
        print("=" * 60)
        print(f"Analysis Time: {analyzer.summary['analysis_time']}")
        print(f"\nSummary:")
        print(f"  Total Scripts : {analyzer.summary['total']}")
        print(f"  ✅ Healthy    : {analyzer.summary['healthy']}")
        print(f"  ⚠️  Warnings  : {analyzer.summary['warnings']}")
        print(f"  ❌ Errors     : {analyzer.summary['errors']}")
        print(f"  📭 No Logs    : {analyzer.summary['no_logs']}")
        print(f"\nScript Status:")
        for r in analyzer.results.values():
            print(f"  {r['num']} - {r['name']}: {r['status']}")
            if r['last_execution']:
                print(f"    Last Run: {r['last_execution']}")
        if analyzer.all_errors:
            print(f"\n⚠️  Issues Requiring Attention:")
            for e in analyzer.all_errors:
                print(f"  - {e}")
        print("\n" + "=" * 60)

        analyzer.send_via_gmail_api()
    finally:
        release_lock()


if __name__ == "__main__":
    main()
