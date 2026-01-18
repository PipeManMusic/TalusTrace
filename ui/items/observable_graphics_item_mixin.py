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
        # Do NOT call super().__init__() to avoid double QGraphicsItem init
        self._observers = []  # List of (event, weakref callback)

    def subscribe(self, event, callback):
        # Use WeakMethod for bound methods, weakref.ref for functions
        if hasattr(callback, '__self__') and callback.__self__ is not None:
            ref = weakref.WeakMethod(callback)
        else:
            ref = weakref.ref(callback)
        self._observers.append((event, ref))

    def unsubscribe(self, event, callback):
        # Remove matching observer
        to_remove = []
        for i, (ev, ref) in enumerate(self._observers):
            cb = ref()
            if ev == event and cb == callback:
                to_remove.append(i)
        for i in reversed(to_remove):
            self._observers.pop(i)

    def notify_observers(self, event, *args, **kwargs):
        # Call all live observers for the event
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
        # Unsubscribe all observers
        self._observers.clear()

    def itemChange(self, change, value):
        # Cleanup on scene removal
        if change == QGraphicsItem.ItemSceneChange and value is None:
            self.cleanup()
        return super().itemChange(change, value)
