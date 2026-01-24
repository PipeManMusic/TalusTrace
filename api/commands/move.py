"""
Move commands for devices and items in Talus Trace.
Implements undoable move operations for devices and scene items.
"""
from infra.undo_stack import BaseCommand
from api.manager import APIManager
from PySide6.QtCore import QPointF

class MoveDeviceCommand(BaseCommand):
    """
    Command to move a device to a new position, supporting undo/redo.
    """
    def __init__(self, device, old_x, old_y, new_x, new_y):
        """
        Initialize the MoveDeviceCommand.
        Args:
            device: The device to move.
            old_x, old_y: Previous coordinates.
            new_x, new_y: New coordinates.
        """
        super().__init__("Move Device")
        self.device = device
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y
        self.api = APIManager.get_instance()

    def execute(self):
        """
        Move the device to the new coordinates and dispatch a model_changed event.
        """
        self.device.x = self.new_x
        self.device.y = self.new_y
        self.api.dispatch("model_changed", {"action": "move", "item": self.device})

    def undo(self):
        """
        Move the device back to the old coordinates and dispatch a model_changed event.
        """
        self.device.x = self.old_x
        self.device.y = self.old_y
        self.api.dispatch("model_changed", {"action": "move", "item": self.device})

class MoveCommand(BaseCommand):
    """
    Command to move a device or scene item, supporting undo/redo.
    """
    def __init__(self, target, old_pos, new_pos):
        """
        Initialize the MoveCommand.
        Args:
            target: Device or scene item to move.
            old_pos: Previous position (tuple or QPointF).
            new_pos: New position (tuple or QPointF).
        """
        super().__init__(description="MoveCommand")
        # Accept both device and scene item for test compatibility
        if hasattr(target, 'model'):
            self.device = target.model
            self.scene_item = target
        else:
            self.device = target
            self.scene_item = None
        self.old_pos = self._normalize_pos(old_pos)
        self.new_pos = self._normalize_pos(new_pos)

    def _normalize_pos(self, pos):
        """
        Normalize a position to a tuple of floats.
        Args:
            pos: QPointF or tuple/list of coordinates.
        Returns:
            Tuple of (x, y) as floats.
        """
        if isinstance(pos, QPointF):
            return (float(pos.x()), float(pos.y()))
        elif isinstance(pos, (tuple, list)) and len(pos) == 2:
            return (float(pos[0]), float(pos[1]))
        return (0.0, 0.0)

    def execute(self):
        """
        Move the device or scene item to the new position and dispatch a model_changed event.
        """
        if self.device:
            self.device.x, self.device.y = self.new_pos
            APIManager.get_instance().dispatch("model_changed", {"action": "move", "item": self.device})

    def undo(self):
        """
        Move the device or scene item back to the old position and dispatch a model_changed event.
        """
        if self.device:
            self.device.x, self.device.y = self.old_pos
            APIManager.get_instance().dispatch("model_changed", {"action": "move", "item": self.device})

    def redo(self):
        """
        Redo the move operation by calling execute().
        """
        self.execute()
