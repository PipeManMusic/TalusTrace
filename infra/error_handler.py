"""
CentralErrorHandler: Centralized Error Handling and Reporting
-----------------------------------------------------------

Usage:
    from infra.error_handler import CentralErrorHandler
    handler = CentralErrorHandler(notification_mgr, log_path)
    try:
        ...
    except Exception as e:
        handler.handle_exception(e, context='optional context')
    # Or use as a decorator:
    @handler.catch_errors
    def my_func(...): ...

Persistence:
    - Errors are logged to a JSONL file via ActionLogger.
    - Notifications are dispatched via NotificationManager.

Maintenance:
    - Extend handle_exception() to add more metadata or escalation logic.
    - For advanced use, subclass CentralErrorHandler or extend its methods.
"""
from infra.action_logger import ActionLogger
from datetime import datetime
import traceback

class CentralErrorHandler:
    """
    Centralized error handling and reporting for Talus Trace.
    Logs errors, dispatches notifications, and provides decorator for error catching.
    """
    def __init__(self, notification_mgr, log_path):
        """
        Initialize the CentralErrorHandler.
        Args:
            notification_mgr: NotificationManager instance for dispatching notifications.
            log_path: Path to the error log file.
        """
        self.logger = ActionLogger(log_path)
        self.notifications = notification_mgr

    def handle_exception(self, exc, context=None):
        """
        Handle an exception: log it and notify via NotificationManager.
        Args:
            exc: Exception object.
            context: Optional context information.
        """
        tb = traceback.format_exc()
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': type(exc).__name__,
            'message': str(exc),
            'traceback': tb,
            'context': context,
        }
        self.logger.log('error', entry)
        self.notifications.notify('error', str(exc), traceback=tb, context=context)

    def catch_errors(self, func):
        """
        Decorator to catch and handle errors in the decorated function.
        Args:
            func: Function to wrap.
        Returns:
            Wrapped function with error handling.
        """
        def wrapper(*args, **kwargs):
            """
            Wrapper function for error catching decorator.
            Catches exceptions, logs them, and re-raises.
            Args:
                *args: Positional arguments for the wrapped function.
                **kwargs: Keyword arguments for the wrapped function.
            Returns:
                Result of the wrapped function, or re-raises exception.
            """
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.handle_exception(e)
                raise
        return wrapper
