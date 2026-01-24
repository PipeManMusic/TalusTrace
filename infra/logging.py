"""
infra/logging.py

Infrastructure logging utilities for Talus Trace.
Provides infra_log for conditional logging based on environment variable.
"""

from logging_config import get_logger
import os

# Environment variable to enable infra logging
INFRA_LOGGING_ENABLED = os.environ.get("TALUSTRACE_INFRA_LOG", "0") == "1"

logger = get_logger("talustrace.infra")

def infra_log(message, level="info"):
    """
    Log a message from the infra layer if logging is enabled.
    Args:
        message (str): The message to log.
        level (str): The log level ('info', 'warning', 'error').
    """
    if not INFRA_LOGGING_ENABLED:
        return
    if level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.info(message)
