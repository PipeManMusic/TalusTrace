
"""
infra/logging.py

Infrastructure logging utilities for Talus Trace.
Provides infra_log for conditional logging based on environment variable.

============================
USAGE AND CONFIGURATION
============================

Enable logging by setting the environment variable:
    export TALUSTRACE_INFRA_LOG=1

Disable logging (default):
    export TALUSTRACE_INFRA_LOG=0
    # or unset TALUSTRACE_INFRA_LOG

Set the log file path (optional):
    export TALUSTRACE_LOG_PATH=/path/to/your/logfile.log
If not set, defaults to 'talustrace_infra.log' in the current directory.

In code, use:
    from infra.logging import infra_log
    infra_log("Your message", level="info")

Levels: "info" (default), "warning", "error", "debug"

If logging is disabled, infra_log will print a message to stdout and do nothing else.
If enabled, messages are appended to the log file and optionally also sent to the Python logger as a fallback.
"""


from logging_config import get_logger
import os

# Environment variable to enable infra logging
INFRA_LOGGING_ENABLED = os.environ.get("TALUSTRACE_INFRA_LOG", "0") == "1"

def get_infra_log_path():
    """
    Return the path to the infra log file, using environment variable if set.
    """
    return os.environ.get("TALUSTRACE_LOG_PATH", "talustrace_infra.log")

logger = get_logger("talustrace.infra")

def infra_log(message, level="info"):
    """
    Log a message from the infra layer if logging is enabled.
    Args:
        message (str): The message to log.
        level (str): The log level ('info', 'warning', 'error').
    """
    enabled = os.environ.get("TALUSTRACE_INFRA_LOG", "0") == "1"
    if not enabled:
        return
    log_path = get_infra_log_path()
    log_entry = f"[{level.upper()}] {message}\n"
    try:
        with open(log_path, "a") as f:
            f.write(log_entry)
    except Exception as e:
        # Fallback to logger if file write fails
        if level == "warning":
            logger.warning(f"infra_log file write failed: {e}; original: {message}")
        elif level == "error":
            logger.error(f"infra_log file write failed: {e}; original: {message}")
        else:
            logger.info(f"infra_log file write failed: {e}; original: {message}")
