"""
MovePinCommand: Command to move a pin to a new position, supporting undo/redo for Talus Trace API.
"""
class MovePinCommand(BaseCommand):
    """Command to move a pin to a new position, supporting undo/redo."""
    def __init__(self, pin, old_pos, new_pos, context=None):
        """Initialize MovePinCommand with pin, old and new positions, and context."""
        BaseCommand.__init__(self, "Move Pin")
        self.pin = pin
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.context = context
        self.api = APIManager.get_instance()
    def execute(self):
        """Move the pin to the new position and dispatch event."""
        self.pin.x, self.pin.y = self.new_pos
        if self.context:
            self.context.observer.dispatch("model_changed", {"action": "move", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "move", "item": self.pin})
    def undo(self):
        """Move the pin back to the old position and dispatch event."""
        self.pin.x, self.pin.y = self.old_pos
        if self.context:
            self.context.observer.dispatch("model_changed", {"action": "move", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "move", "item": self.pin})
