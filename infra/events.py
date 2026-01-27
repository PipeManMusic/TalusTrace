"""
Event Manager Design:
---------------------
The EventManager provides a publish/subscribe (pub/sub) system for decoupled communication between components. Events can be emitted from any part of the application and received by any interested listeners, without direct references. This enables modularity, extensibility, and testability, as new features can subscribe to or emit events without modifying core logic. The EventManager supports event filtering, propagation, and integration with undo/redo and logging systems.
"""
"""
infra/events.py

Event hooks/signals for bundle and wire actions (split, merge, serialize, etc).
"""
from typing import Callable, Dict, List

class EventHook:
    """
    EventHook provides a simple event subscription and notification system.
    Subscribers can register callbacks to be notified when the event is fired.
    """
    def __init__(self):
        """
        Initialize the EventHook with an empty list of subscribers.
        """
        self._subscribers: List[Callable] = []
    def subscribe(self, fn: Callable):
        """
        Subscribe a callback function to the event.
        Args:
            fn (Callable): The function to call when the event is fired.
        """
        self._subscribers.append(fn)
    def unsubscribe(self, fn: Callable):
        """
        Unsubscribe a callback function from the event.
        Args:
            fn (Callable): The function to remove from subscribers.
        """
        self._subscribers.remove(fn)
    def fire(self, *args, **kwargs):
        """
        Fire the event, calling all subscriber functions with the provided arguments.
        """
        for fn in self._subscribers:
            fn(*args, **kwargs)


# Example global event hooks
on_bundle_split = EventHook()
on_bundle_merge = EventHook()
on_bundle_serialize = EventHook()

# Wire event hooks:
# on_wire_split: (wire, old_segment_uuid, new_node, (left_uuid, right_uuid))
on_wire_split = EventHook()
# on_wire_merge: (wire, left_segment_uuid, merged_uuid)
on_wire_merge = EventHook()
on_wire_serialize = EventHook()
