from infra.undo_stack import BaseCommand
from api.manager import APIManager
from PySide6.QtCore import QPointF

class MoveDeviceCommand(BaseCommand):
    def __init__(self, device, old_x, old_y, new_x, new_y):
        super().__init__("Move Device")
        self.device = device
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y
        self.api = APIManager.get_instance()

    def execute(self):
        self.device.x = self.new_x
        self.device.y = self.new_y
        self.api.dispatch("model_changed", {"action": "move", "item": self.device})

    def undo(self):
        self.device.x = self.old_x
        self.device.y = self.old_y
        self.api.dispatch("model_changed", {"action": "move", "item": self.device})

class MoveCommand(BaseCommand):
    def __init__(self, target, old_pos, new_pos):
        super().__init__(description="MoveCommand")
        self.target = target
        self.old_pos = self._normalize_pos(old_pos)
        self.new_pos = self._normalize_pos(new_pos)

    def _normalize_pos(self, pos):
        if isinstance(pos, QPointF):
            return (float(pos.x()), float(pos.y()))
        elif isinstance(pos, (tuple, list)) and len(pos) == 2:
            return (float(pos[0]), float(pos[1]))
        return (0.0, 0.0)

    def execute(self):
        self._set_pos(self.new_pos)

    def undo(self):
        self._set_pos(self.old_pos)

    def _set_pos(self, pos):
        # Prioritize model attributes
        if hasattr(self.target, 'x') and hasattr(self.target, 'y'):
            self.target.x, self.target.y = pos
        # Also update QGraphicsItem if present
        if hasattr(self.target, 'setPos'):
            self.target.setPos(QPointF(pos[0], pos[1]))
