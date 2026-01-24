"""
ActionLogger: Persistent Action/Event Logging Utility
-----------------------------------------------------

Usage:
    from infra.action_logger import ActionLogger
    logger = ActionLogger(log_path)
    logger.log('event_type', {'key': 'value'})
    for entry in logger.read_log():
        ...
    for entry in logger.filter_events('event_type'):
        ...

Persistence:
    - Logs actions/events to a JSONL file at the given path.
    - Each entry includes a UTC timestamp, event type, and payload.

Maintenance:
    - Extend log() to add more metadata if needed.
    - Log files can be rotated or archived externally.
    - For advanced use, subclass ActionLogger or extend its methods.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

class ActionLogger:
    """
    Persistent action/event logging utility for Talus Trace.
    Logs actions/events to a JSONL file and provides filtering and reading utilities.
    """
    def __init__(self, log_path: Path):
        """
        Initialize the ActionLogger.
        Args:
            log_path: Path to the log file.
        """
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, payload: Optional[Dict[str, Any]] = None):
        """
        Log an event with the given type and payload.
        Args:
            event_type: Type of the event.
            payload: Optional dictionary of event data.
        """
        # Use timezone-aware UTC datetime to avoid deprecation warning
        from datetime import datetime, timezone
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload or {},
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def read_log(self):
        """
        Read all log entries from the log file.
        Yields:
            Parsed log entry dictionaries.
        """
        with open(self.log_path, "r") as f:
            for line in f:
                yield json.loads(line)

    def filter_events(self, event_type: str):
        """
        Filter log entries by event type.
        Args:
            event_type: Type of event to filter.
        Returns:
            Iterator over matching log entries.
        """
        return (entry for entry in self.read_log() if entry["event_type"] == event_type)
