"""
Shared utilities for all automation scripts.
Provides logging, error handling, email notifications, and database management.
"""

import os
import sys
import logging
import smtplib
import socket
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables — explicit path ensures LaunchAgent finds .env
# regardless of working directory at time of execution
_ENV_FILE = Path.home() / "Automations" / "config" / ".env"
if _ENV_FILE.exists():
    load_dotenv(str(_ENV_FILE))
else:
    load_dotenv()  # Fallback: search current directory (works in dev/testing)

# ============================================================================
# Network Connectivity Gate
# ============================================================================

def check_network_connectivity(
    logger: Optional[logging.Logger] = None,
    host: str = "www.google.com",
    port: int = 443,
    max_attempts: int = 5,
    wait_seconds: int = 10,
) -> bool:
    """
    Gate API calls on verified network connectivity.

    Early-morning LaunchAgent fires can race the Mac's network coming online,
    causing DNS failures like "Unable to find the server at sheets.googleapis.com".
    Call this at the top of main() before any outbound API call.

    Retries up to max_attempts times with wait_seconds between attempts. On
    success returns True. On exhausted retries logs a warning and calls
    sys.exit(0) so the LaunchAgent records a clean exit and retries on its
    next scheduled run rather than looping on an immediate failure.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            with socket.create_connection((host, port), timeout=5):
                if logger:
                    logger.info(
                        f"Network connectivity confirmed on attempt {attempt}/{max_attempts}"
                    )
                return True
        except OSError as exc:
            if logger:
                logger.info(
                    f"Network check attempt {attempt}/{max_attempts} failed: {exc}"
                )
            if attempt < max_attempts:
                time.sleep(wait_seconds)

    if logger:
        logger.warning(
            f"Network connectivity not confirmed after {max_attempts} attempts; "
            f"exiting cleanly. LaunchAgent will retry on next scheduled run."
        )
    sys.exit(0)


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logger(script_name: str) -> logging.Logger:
    """
    Set up a logger for a specific automation script.
    
    Args:
        script_name: Name of the script (used for log file naming)
        
    Returns:
        Configured logger instance
    """
    log_dir = Path(os.getenv("LOG_DIR", "/Users/kevinmassengill/Automations/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = log_dir / f"{script_name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger(script_name)
    logger.setLevel(getattr(logging, log_level))
    
    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# ============================================================================
# Centralized Credentials Loader
# ============================================================================

def load_credentials() -> Dict[str, Any]:
    """
    Centralized credentials loader for all scripts.

    Loads environment variables from ~/Automations/config/.env with an
    explicit path so LaunchAgent-run scripts always find the file regardless
    of the working directory at execution time.

    Returns:
        dict: Dictionary of all loaded credentials and config paths.

    Raises:
        FileNotFoundError: If .env file not found.
        ValueError: If critical credentials (AIRTABLE_API_KEY) are missing.
    """
    env_file = Path.home() / "Automations" / "config" / ".env"

    if not env_file.exists():
        raise FileNotFoundError(
            f"Credentials file not found at {env_file}. "
            f"Please create {env_file} with your API keys."
        )

    load_dotenv(str(env_file), override=True)

    # Verify critical credentials
    required_keys = ["AIRTABLE_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    if missing_keys:
        raise ValueError(
            f"Missing required credentials in {env_file}: {', '.join(missing_keys)}"
        )

    return {
        # Airtable
        "AIRTABLE_API_KEY": os.getenv("AIRTABLE_API_KEY"),
        "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID", "appoNkgoKHAUXgXV9"),
        "AIRTABLE_TABLE_ID": os.getenv("AIRTABLE_TABLE_ID", "tblxEhVek8ldTQMW1"),

        # Gmail / Google OAuth
        "GOOGLE_TOKEN_FILE": os.getenv(
            "GOOGLE_TOKEN_FILE",
            str(Path.home() / "Automations" / "config" / "google_token.json")
        ),
        "GOOGLE_CREDS_FILE": os.getenv(
            "GOOGLE_CREDS_FILE",
            str(Path.home() / "Automations" / "config" / "oauth_credentials.json")
        ),

        # ClickUp
        "CLICKUP_API_KEY": os.getenv("CLICKUP_API_KEY"),
        "CLICKUP_TEAM_ID": os.getenv("CLICKUP_TEAM_ID"),

        # Clay enrichment
        "CLAY_API_KEY": os.getenv("CLAY_API_KEY"),

        # Claude / AI
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
        "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),

        # OpenAI (Script 7)
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),

        # Paths
        "AUTOMATION_BASE_PATH": str(Path.home() / "Automations"),
        "CONFIG_DIR": str(Path.home() / "Automations" / "config"),
        "LOGS_DIR": str(Path.home() / "Automations" / "logs"),
        "STATE_DB_PATH": str(Path.home() / "Automations" / "config" / "state.db"),
    }


# ============================================================================
# Email Notifications
# ============================================================================

def send_error_notification(
    script_name: str,
    error_message: str,
    error_details: str = "",
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Send an error notification email to the configured recipient.
    
    Args:
        script_name: Name of the script that encountered the error
        error_message: Brief error message
        error_details: Detailed error information (traceback, etc.)
        logger: Logger instance for logging the notification attempt
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        sender_email = os.getenv("NOTIFICATION_EMAIL")
        sender_password = os.getenv("NOTIFICATION_EMAIL_PASSWORD")
        recipient_email = os.getenv("NOTIFICATION_EMAIL")
        
        if not all([sender_email, sender_password, recipient_email]):
            if logger:
                logger.warning("Email notification credentials not configured. Skipping notification.")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = f"[AUTOMATION ERROR] {script_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""
Automation Script Error Report
================================

Script: {script_name}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Error Message:
{error_message}

Details:
{error_details if error_details else "No additional details available."}

---
This is an automated notification from your local automation system.
"""
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        if logger:
            logger.info(f"Error notification sent to {recipient_email}")
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to send error notification: {str(e)}")
        return False


# ============================================================================
# State Management (SQLite Database)
# ============================================================================

class StateManager:
    """Manages script state using SQLite database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the state manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path or os.getenv("STATE_DB_PATH", "/Users/kevinmassengill/Automations/config/state.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for tracking last processed items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS script_state (
                    script_name TEXT PRIMARY KEY,
                    last_processed_id TEXT,
                    last_processed_timestamp TEXT,
                    last_run_timestamp TEXT,
                    status TEXT,
                    error_count INTEGER DEFAULT 0,
                    updated_at TEXT
                )
            """)
            
            # Table for tracking API rate limits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_rate_limits (
                    api_name TEXT PRIMARY KEY,
                    calls_made INTEGER DEFAULT 0,
                    reset_timestamp TEXT,
                    updated_at TEXT
                )
            """)
            
            conn.commit()
    
    def get_state(self, script_name: str) -> Dict[str, Any]:
        """
        Get the current state for a script.
        
        Args:
            script_name: Name of the script
            
        Returns:
            Dictionary containing the script state
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM script_state WHERE script_name = ?",
                (script_name,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return {
                "script_name": script_name,
                "last_processed_id": None,
                "last_processed_timestamp": None,
                "last_run_timestamp": None,
                "status": "never_run",
                "error_count": 0
            }
    
    def update_state(
        self,
        script_name: str,
        last_processed_id: Optional[str] = None,
        last_processed_timestamp: Optional[str] = None,
        status: str = "success",
        error_count: int = 0
    ):
        """
        Update the state for a script.
        
        Args:
            script_name: Name of the script
            last_processed_id: ID of the last processed item
            last_processed_timestamp: Timestamp of the last processed item
            status: Current status (success, error, running, etc.)
            error_count: Number of consecutive errors
        """
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if record exists
            cursor.execute(
                "SELECT script_name FROM script_state WHERE script_name = ?",
                (script_name,)
            )
            exists = cursor.fetchone() is not None
            
            if exists:
                cursor.execute("""
                    UPDATE script_state
                    SET last_processed_id = ?,
                        last_processed_timestamp = ?,
                        last_run_timestamp = ?,
                        status = ?,
                        error_count = ?,
                        updated_at = ?
                    WHERE script_name = ?
                """, (
                    last_processed_id,
                    last_processed_timestamp,
                    now,
                    status,
                    error_count,
                    now,
                    script_name
                ))
            else:
                cursor.execute("""
                    INSERT INTO script_state
                    (script_name, last_processed_id, last_processed_timestamp, last_run_timestamp, status, error_count, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    script_name,
                    last_processed_id,
                    last_processed_timestamp,
                    now,
                    status,
                    error_count,
                    now
                ))
            
            conn.commit()
    
    def increment_error_count(self, script_name: str):
        """Increment the error count for a script."""
        state = self.get_state(script_name)
        self.update_state(
            script_name,
            last_processed_id=state.get("last_processed_id"),
            last_processed_timestamp=state.get("last_processed_timestamp"),
            status="error",
            error_count=state.get("error_count", 0) + 1
        )
    
    def reset_error_count(self, script_name: str):
        """Reset the error count for a script."""
        state = self.get_state(script_name)
        self.update_state(
            script_name,
            last_processed_id=state.get("last_processed_id"),
            last_processed_timestamp=state.get("last_processed_timestamp"),
            status="success",
            error_count=0
        )


# ============================================================================
# Error Handling Decorator
# ============================================================================

def handle_errors(script_name: str, logger: Optional[logging.Logger] = None):
    """
    Decorator to handle errors in automation scripts.
    Logs errors, sends notifications, and manages error counts.
    
    Args:
        script_name: Name of the script
        logger: Logger instance
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            state_manager = StateManager()
            try:
                result = func(*args, **kwargs)
                state_manager.reset_error_count(script_name)
                return result
            except Exception as e:
                error_msg = f"Error in {script_name}: {str(e)}"
                error_details = f"Function: {func.__name__}\nException: {type(e).__name__}\n{str(e)}"
                
                if logger:
                    logger.error(error_msg, exc_info=True)
                else:
                    print(f"ERROR: {error_msg}")
                
                # Send notification
                send_error_notification(script_name, error_msg, error_details, logger)
                
                # Increment error count
                state_manager.increment_error_count(script_name)
                
                raise
        
        return wrapper
    return decorator


# ============================================================================
# API Client Base Classes
# ============================================================================

class APIClient:
    """Base class for API clients with error handling and logging."""
    
    def __init__(self, api_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the API client.
        
        Args:
            api_name: Name of the API
            logger: Logger instance
        """
        self.api_name = api_name
        self.logger = logger or setup_logger(api_name)
        self.state_manager = StateManager()
    
    def log_api_call(self, endpoint: str, method: str = "GET"):
        """Log an API call."""
        if self.logger:
            self.logger.debug(f"API Call: {method} {endpoint}")
    
    def handle_api_error(self, error: Exception, endpoint: str):
        """Handle API errors with logging and notifications."""
        error_msg = f"API Error in {self.api_name}: {str(error)}"
        if self.logger:
            self.logger.error(error_msg, exc_info=True)
        send_error_notification(self.api_name, error_msg, str(error), self.logger)


if __name__ == "__main__":
    # Test the shared utilities
    logger = setup_logger("test_script")
    logger.info("Shared utilities module loaded successfully")
    
    state_manager = StateManager()
    state_manager.update_state("test_script", last_processed_id="123", status="success")
    state = state_manager.get_state("test_script")
    print(f"State: {state}")
