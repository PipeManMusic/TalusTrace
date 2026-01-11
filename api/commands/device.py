from api.manager import APIManager
from infra.undo_stack import BaseCommand
from api.actions import register_action
from core.device import Pin
from core.selection import SelectionManager

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

class AddWireCommand(BaseCommand):
    def __init__(self, wire):
        super().__init__("Add Wire")
        self.wire = wire
        self.api = APIManager.get_instance()

    def execute(self):
        self.api.context.harness.wires.append(self.wire)
        self.api.dispatch("model_changed", {"action": "add", "item": self.wire})

    def undo(self):
        if self.wire in self.api.context.harness.wires:
            self.api.context.harness.wires.remove(self.wire)
        self.api.dispatch("model_changed", {"action": "remove", "item": self.wire})

class AddPinCommand(BaseCommand):
    def __init__(self, device):
        super().__init__("Add Pin")
        self.device = device
        self.api = APIManager.get_instance()
        self.new_pin = None

    def execute(self):
        # 1. Determine Position (Right edge, stacked)
        # Check if 'width_mm' is in meta, default to 40.0 if not found
        width = self.device.meta.get("width_mm", 40.0) if hasattr(self.device, 'meta') else 40.0
        
        # Count existing pins to stack them vertically
        count = len(self.device.pins)
        pin_spacing = 5.0
        
        # Position: X = Width (Right Edge), Y = 5mm + (Index * 5mm)
        x = width
        y = 5.0 + (count * pin_spacing)
        
        # Create Pin ID
        pin_id = f"{len(self.device.pins) + 1}"
        
        # 2. Create and Append
        self.new_pin = Pin(id=pin_id, x=x, y=y)
        self.device.pins.append(self.new_pin)
        
        # 3. Notify
        self.api.dispatch("model_changed", {"action": "update", "item": self.device})

    def undo(self):
        if self.new_pin in self.device.pins:
            self.device.pins.remove(self.new_pin)
        self.api.dispatch("model_changed", {"action": "update", "item": self.device})

# --- Actions ---

@register_action("device.add_pin")
def device_add_pin(context):
    mgr = SelectionManager()
    selection = mgr.selected_models
    if not selection: return

    # Filter for devices (items that have a 'pins' list)
    devices = [item for item in selection if hasattr(item, 'pins')]
    if not devices: return

    # Apply to the first selected device
    target = devices[0]
    cmd = AddPinCommand(target)
    APIManager.get_instance().context.undo_stack.push(cmd)