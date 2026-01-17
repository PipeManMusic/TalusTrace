from infra.undo_stack import BaseCommand
from api.manager import APIManager

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
