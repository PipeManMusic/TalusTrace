
"""
ObservableGraphicsItemMixin: Adds observer pattern support to QGraphicsItems.
Manages observer callbacks with weak references and handles cleanup on scene removal.
"""
import weakref
from PySide6.QtWidgets import QGraphicsItem

class ObservableGraphicsItemMixin:
    """
    Mixin for QGraphicsItems that need robust observer management and cleanup.
    - Uses weakref for all observer callbacks.
    - Handles cleanup on scene removal via itemChange.
    - Provides a cleanup() method for subclasses to extend.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the mixin and set up the observer list.
        Note: Does not call super().__init__() to avoid double QGraphicsItem init.
        """
        self._observers = []  # List of (event, weakref callback)

    def subscribe(self, event, callback):
        """
        Subscribe a callback to an event. Uses weak references for callbacks.
        Args:
            event: The event name or type.
            callback: The function or method to call when the event occurs.
        """
        if hasattr(callback, '__self__') and callback.__self__ is not None:
            ref = weakref.WeakMethod(callback)
        else:
            ref = weakref.ref(callback)
        self._observers.append((event, ref))

    def unsubscribe(self, event, callback):
        """
        Unsubscribe a callback from an event.
        Args:
            event: The event name or type.
            callback: The function or method to remove.
        """
        to_remove = []
        for i, (ev, ref) in enumerate(self._observers):
            cb = ref()
            if ev == event and cb == callback:
                to_remove.append(i)
        for i in reversed(to_remove):
            self._observers.pop(i)

    def notify_observers(self, event, *args, **kwargs):
        """
        Notify all observers subscribed to the given event.
        Args:
            event: The event name or type.
            *args: Positional arguments to pass to the callback.
            **kwargs: Keyword arguments to pass to the callback.
        """
        dead = []
        for i, (ev, ref) in enumerate(self._observers):
            if ev == event:
                cb = ref()
                if cb is not None:
                    cb(*args, **kwargs)
                else:
                    dead.append(i)
        for i in reversed(dead):
            self._observers.pop(i)

    def cleanup(self):
        """
        Unsubscribe all observers and clear the observer list.
        """
        self._observers.clear()

    def itemChange(self, change, value):
        """
        Handle QGraphicsItem itemChange events. Cleans up observers on scene removal.
        Args:
            change: The type of change.
            value: The value associated with the change.
        Returns:
            The result of the base class itemChange.
        """
        if change == QGraphicsItem.ItemSceneChange and value is None:
            self.cleanup()
        return super().itemChange(change, value)
