from api.manager import APIManager
from infra.undo_stack import BaseCommand

class AddDeviceCommand(BaseCommand):
    def __init__(self, device):
        super().__init__("Add Device")
        self.device = device
        self.api = APIManager.get_instance()

    def execute(self):
        # 1. Update Model
        self.api.context.harness.devices.append(self.device)
        # 2. Notify System (Canvas and Browser will hear this)
        self.api.dispatch("model_changed", {"action": "add", "item": self.device})

    def undo(self):
        # 1. Update Model
        if self.device in self.api.context.harness.devices:
            self.api.context.harness.devices.remove(self.device)
        # 2. Notify System
        self.api.dispatch("model_changed", {"action": "remove", "item": self.device})
