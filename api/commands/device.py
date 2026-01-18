import uuid
from api.manager import APIManager
from infra.undo_stack import BaseCommand
from api.actions import register_action
# FIXED: Import from core.pin, not core.device
from core.pin import Pin
from core.selection import SelectionManager

class AddDeviceCommand(BaseCommand):
    def __init__(self, device):
        super().__init__("Add Device")
        self.device = device
        self.api = APIManager.get_instance()

    def execute(self):
        self.api.context.harness.devices.append(self.device)
        self.api.dispatch("device_added", self.device)
        self.api.dispatch("model_changed", {"action": "add", "item": self.device})

    def undo(self):
        if self.device in self.api.context.harness.devices:
            self.api.context.harness.devices.remove(self.device)
            self.api.dispatch("device_removed", self.device)
        self.api.dispatch("model_changed", {"action": "remove", "item": self.device})

class AddWireCommand(BaseCommand):
    def __init__(self, wire):
        super().__init__("Add Wire")
        self.wire = wire
        self.api = APIManager.get_instance()

    def execute(self):
        self.api.context.harness.wires.append(self.wire)
        self.api.dispatch("wire_added", self.wire)
        self.api.dispatch("model_changed", {"action": "add", "item": self.wire})

    def undo(self):
        if self.wire in self.api.context.harness.wires:
            self.api.context.harness.wires.remove(self.wire)
            self.api.dispatch("wire_removed", self.wire)
        self.api.dispatch("model_changed", {"action": "remove", "item": self.wire})

class AddPinCommand(BaseCommand):
    def __init__(self, device):
        super().__init__("Add Pin")
        self.device = device
        self.api = APIManager.get_instance()
        self.new_pin = None

    def execute(self):
        width = self.device.meta.get("width_mm", 40.0) if hasattr(self.device, 'meta') else 40.0
        count = len(self.device.pins)
        pin_spacing = 5.0
        x = width
        y = 5.0 + (count * pin_spacing)
        pin_id = f"PIN_{str(uuid.uuid4())[:8]}"
        pin_label = str(count + 1)
        self.new_pin = Pin(
            id=pin_id,
            label=pin_label,
            x=x,
            y=y,
            device_id=self.device.id
        )
        self.device.pins.append(self.new_pin)
        self.api.dispatch("pin_added", self.new_pin)
        self.api.dispatch("device_updated", self.device)
        self.api.dispatch("model_changed", {"action": "update", "item": self.device})

    def undo(self):
        if self.new_pin in self.device.pins:
            self.device.pins.remove(self.new_pin)
            self.api.dispatch("pin_removed", self.new_pin)
            self.api.dispatch("device_updated", self.device)
        self.api.dispatch("model_changed", {"action": "update", "item": self.device})

# --- Actions ---

@register_action("device.add_pin")
def device_add_pin(context):
    mgr = SelectionManager()
    selection = mgr.selected_models
    if not selection: return

    devices = [item for item in selection if hasattr(item, 'pins')]
    if not devices: return

    target = devices[0]
    cmd = AddPinCommand(target)
    APIManager.get_instance().context.undo_stack.push(cmd)