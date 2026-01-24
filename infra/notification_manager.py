"""
NotificationManager: Notification and Logging Infrastructure
---------------------------------------------------------

Usage:
    from infra.notification_manager import NotificationManager
    mgr = NotificationManager(log_path)
    mgr.notify('info', 'Welcome!')
    mgr.notify('error', 'Something went wrong.')
    all_notes = list(mgr.list_notifications())
    mgr.clear_notifications()

Persistence:
    - Notifications are logged to a JSONL file via ActionLogger.
    - Each notification includes a timestamp, type, and message.

Maintenance:
    - Extend notify() to add more metadata if needed.
    - For advanced use, subclass NotificationManager or extend its methods.
"""
from infra.action_logger import ActionLogger
from datetime import datetime

class NotificationManager:
    """
    Notification and logging infrastructure for Talus Trace.
    Manages notifications, logs them, and dispatches to hooks.
    """
    def __init__(self, log_path, dispatch_hooks=None):
        """
        Initialize the NotificationManager.
        Args:
            log_path: Path to the notification log file.
            dispatch_hooks: Optional list of callables for dispatching notifications.
        """
        self.logger = ActionLogger(log_path)
        self._notifications = []
        self._dispatch_hooks = dispatch_hooks or []  # List of callables for UI, etc.

    def notify(self, level, message, **kwargs):
        """
        Send a notification, log it, and dispatch to hooks.
        Args:
            level: Notification level (e.g., 'info', 'error').
            message: Notification message.
            **kwargs: Additional metadata for the notification.
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
        }
        entry.update(kwargs)
        self._notifications.append(entry)
        self.logger.log('notification', entry)
        for hook in self._dispatch_hooks:
            try:
                hook(entry)
            except Exception:
                pass

    def list_notifications(self, persisted=False):
        """
        List notifications. If persisted=True, read from log file for full history.
        Args:
            persisted: If True, read notifications from log file.
        Returns:
            Iterator over notifications.
        """
        if not persisted:
            return iter(self._notifications)
        # Read from log file
        return (entry['payload'] for entry in self.logger.read_log() if entry.get('event_type') == 'notification')

    def clear_notifications(self, persisted=False):
        """
        Clear notifications from memory and optionally from log file.
        Args:
            persisted: If True, clear persisted notifications (truncate log file).
        """
        self._notifications.clear()
        # Optionally, clear persisted notifications (truncate log file)
        if persisted:
            # This will clear all log entries, not just notifications
            open(self.logger.log_path, 'w').close()
