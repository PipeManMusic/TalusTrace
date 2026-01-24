"""
Logging configuration for Talus Trace.

Sets up logging handlers, log level, and log format based on environment variables.
"""
import logging
import os

LOG_LEVEL = os.environ.get("TALUSTRACE_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("TALUSTRACE_LOG_FORMAT", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
LOG_FILE = os.environ.get("TALUSTRACE_LOG_FILE")

handlers = []
if LOG_FILE:
    handlers.append(logging.FileHandler(LOG_FILE))
else:
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    handlers=handlers
)

def get_logger(name):
    """Get a logger with the specified name, using the configured logging settings."""
    return logging.getLogger(name)
