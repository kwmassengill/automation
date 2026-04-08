"""
Script 10T: MHC-10T Meeting Intelligence Trigger
Purpose: Webhook receiver to trigger Script 10 (Pre-Meeting Intelligence)
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

sys.path.insert(0, str(Path(__file__).parent))
try:
    from shared_utils import setup_logger, StateManager, send_error_notification
except ImportError:
    import logging
    def setup_logger(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    class StateManager:
        def get_state(self, name): return {}
        def update_state(self, name, **kwargs): pass
        
    def send_error_notification(name, msg, details="", logger=None):
        if logger: logger.error(f"Notification: {msg}\n{details}")

SCRIPT_NAME = "script_10t_meeting_intelligence_trigger"

env_file = Path.home() / "Automations" / "config" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

logger = setup_logger(SCRIPT_NAME)
state_manager = StateManager()

app = FastAPI(title="Meeting Intelligence Trigger API")

processed_meetings = {}
CACHE_TTL_MINUTES = 60

def clean_cache():
    now = time.time()
    expired_keys = [k for k, v in processed_meetings.items() if v < now]
    for k in expired_keys:
        del processed_meetings[k]

def is_duplicate(meeting_id: str) -> bool:
    clean_cache()
    if meeting_id in processed_meetings:
        return True
    processed_meetings[meeting_id] = time.time() + (CACHE_TTL_MINUTES * 60)
    return False

def run_script_10(meeting_data: Dict[str, Any]):
    logger.info(f"Starting Script 10 for meeting: {meeting_data.get('meeting_title', 'Unknown')}")
    
    try:
        temp_dir = Path.home() / "Automations" / "tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file = temp_dir / f"meeting_data_{int(time.time())}.json"
        with open(temp_file, "w") as f:
            json.dump(meeting_data, f)
            
        runner_script = temp_dir / f"runner_{int(time.time())}.py"
        with open(runner_script, "w") as f:
            f.write(f"""
import sys
import json
from pathlib import Path

sys.path.insert(0, "{Path(__file__).parent}")

from script_10_mhc10_meeting_intelligence_summary import process_meeting_intelligence

with open("{temp_file}", "r") as f:
    meeting_data = json.load(f)

try:
    result = process_meeting_intelligence(meeting_data)
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
    sys.exit(1)
""")
        
        logger.info(f"Executing runner script: {runner_script}")
        process = subprocess.Popen(
            [sys.executable, str(runner_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"Script 10 completed successfully. Output: {stdout.strip()}")
            state_manager.update_state(
                SCRIPT_NAME, 
                last_processed_id=meeting_data.get("airtable_record_id", "unknown"),
                status="success"
            )
        else:
            error_msg = f"Script 10 failed with return code {process.returncode}. Stderr: {stderr}"
            logger.error(error_msg)
            send_error_notification(SCRIPT_NAME, "Script 10 Execution Failed", error_msg, logger)
            state_manager.update_state(
                SCRIPT_NAME, 
                last_processed_id=meeting_data.get("airtable_record_id", "unknown"),
                status="error"
            )
            
    except Exception as e:
        error_msg = f"Failed to spawn Script 10: {str(e)}"
        logger.error(error_msg, exc_info=True)
        send_error_notification(SCRIPT_NAME, "Failed to spawn Script 10", error_msg, logger)
    finally:
        try:
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            if 'runner_script' in locals() and runner_script.exists():
                runner_script.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/webhook/meeting-intelligence")
async def webhook_meeting_intelligence(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        logger.info(f"Received webhook payload: {json.dumps(payload)[:200]}...")
        
        contact_name = payload.get("contact_name")
        company_name = payload.get("company_name")
        airtable_record_id = payload.get("airtable_record_id")
        full_briefing_text = payload.get("full_briefing_text")
        
        if not all([contact_name, company_name, airtable_record_id, full_briefing_text]):
            missing = [k for k, v in {
                "contact_name": contact_name, 
                "company_name": company_name, 
                "airtable_record_id": airtable_record_id, 
                "full_briefing_text": full_briefing_text
            }.items() if not v]
            
            error_msg = f"Missing required fields: {', '.join(missing)}"
            logger.warning(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        meeting_id = f"{airtable_record_id}_{payload.get('meeting_date', 'nodate')}"
        if is_duplicate(meeting_id):
            logger.info(f"Duplicate trigger detected for meeting ID: {meeting_id}. Ignoring.")
            return JSONResponse(
                status_code=200, 
                content={"status": "ignored", "reason": "duplicate", "meeting_id": meeting_id}
            )
        
        background_tasks.add_task(run_script_10, payload)
        
        return JSONResponse(
            status_code=202, 
            content={
                "status": "accepted", 
                "message": "Meeting intelligence processing started in background",
                "meeting_id": meeting_id
            }
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/webhook/make-compat")
async def webhook_make_compat(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        logger.info(f"Received Make.com compat webhook payload")
        
        meeting_data = {
            "contact_name": payload.get("contact_name", "Unknown"),
            "company_name": payload.get("company_name", "Unknown"),
            "meeting_title": payload.get("meeting_title", "Meeting"),
            "meeting_date": payload.get("meeting_datetime", "").split("T")[0] if "T" in payload.get("meeting_datetime", "") else payload.get("meeting_datetime", ""),
            "airtable_record_id": payload.get("airtable_record_id", ""),
            "full_briefing_text": payload.get("full_briefing_text", "")
        }
        
        meeting_id = f"{meeting_data['airtable_record_id']}_{meeting_data['meeting_date']}"
        if is_duplicate(meeting_id):
            logger.info(f"Duplicate trigger detected for meeting ID: {meeting_id}. Ignoring.")
            return JSONResponse(
                status_code=200, 
                content={"status": "ignored", "reason": "duplicate", "meeting_id": meeting_id}
            )
            
        background_tasks.add_task(run_script_10, meeting_data)
        
        return JSONResponse(
            status_code=202, 
            content={
                "status": "accepted", 
                "message": "Meeting intelligence processing started in background",
                "meeting_id": meeting_id
            }
        )
        
    except Exception as e:
        logger.error(f"Make compat webhook error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    port = int(os.getenv("WEBHOOK_PORT", 8000))
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    
    logger.info(f"Starting {SCRIPT_NAME} on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
