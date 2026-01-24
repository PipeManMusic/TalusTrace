"""
Device, pin, and wire command implementations for Talus Trace API.
Implements command patterns for APIManager, supporting undo/redo and event dispatch.
"""

from infra.undo_stack import BaseCommand
from api.manager import APIManager
from core.harness import DeviceList
from core.pin import Pin
import uuid
from api.actions import register_action
from core.selection import SelectionManager

"""
Device, pin, and wire command implementations for Talus Trace API.
Implements command patterns for APIManager, supporting undo/redo and event dispatch.
"""

class AddDeviceCommand(BaseCommand):
    """Command to add a device to the harness, supporting undo/redo."""
    def __init__(self, device, context=None, **kwargs):
        """Initialize AddDeviceCommand with device and optional context."""
        BaseCommand.__init__(self, "Add Device")
        self.device = device
        self.context = context
        self.api = APIManager.get_instance()

    def execute(self):
        """Add the device to the harness and dispatch event."""
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        with DeviceList.test_bypass():
            if self.device not in harness.devices:
                harness.devices.append(self.device)
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "add", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "add", "item": self.device})
        self.api.dispatch("device_added", self.device)

    def undo(self):
        """Remove the device from the harness and dispatch event."""
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        with DeviceList.test_bypass():
            if self.device in harness.devices:
                harness.devices.remove(self.device)
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "delete", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "delete", "item": self.device})
        self.api.dispatch("device_removed", self.device)

class MovePinCommand(BaseCommand):
    """Command to move a pin to a new position, supporting undo/redo."""
    def __init__(self, pin, old_pos, new_pos, context=None):
        """Initialize MovePinCommand with pin, old and new positions, and optional context."""
        BaseCommand.__init__(self, "Move Pin")
        self.pin = pin
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.context = context
        self.api = APIManager.get_instance()

    def execute(self):
        """Move the pin to the new position and dispatch 'move' event."""
        self.pin.x, self.pin.y = self.new_pos
        # Always use the observer from the context passed to the command, if available
        observer = getattr(self.context, "observer", None)
        if observer:
            observer.dispatch("model_changed", {"action": "move", "item": self.pin})
        else:
            api_ctx = getattr(self.api, "context", None)
            api_observer = getattr(api_ctx, "observer", None) if api_ctx else None
            if api_observer:
                api_observer.dispatch("model_changed", {"action": "move", "item": self.pin})
            else:
                self.api.dispatch("model_changed", {"action": "move", "item": self.pin})

    def undo(self):
        """Move the pin back to the old position and dispatch 'move' event."""
        self.pin.x, self.pin.y = self.old_pos
        observer = getattr(self.context, "observer", None)
        if observer:
            observer.dispatch("model_changed", {"action": "move", "item": self.pin})
        else:
            api_ctx = getattr(self.api, "context", None)
            api_observer = getattr(api_ctx, "observer", None) if api_ctx else None
            if api_observer:
                api_observer.dispatch("model_changed", {"action": "move", "item": self.pin})
            else:
                self.api.dispatch("model_changed", {"action": "move", "item": self.pin})

class AddWireCommand(BaseCommand):
    """Command to add a wire to the harness, supporting undo/redo."""
    def __init__(self, wire, context=None, **kwargs):
        """Initialize AddWireCommand with wire, context, and optional positions."""
        BaseCommand.__init__(self, "Add Wire")
        self.wire = wire
        self.context = context
        self.api = APIManager.get_instance()
        self.new_pos = kwargs.get('new_pos', None)
        self.old_pos = kwargs.get('old_pos', None)

    def execute(self):
        """Execute the wire addition command and emit 'add' event."""
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        if self.wire not in harness.wires:
            harness.wires.append(self.wire)
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "add", "item": self.wire})
        else:
            self.api.dispatch("model_changed", {"action": "add", "item": self.wire})
        self.api.dispatch("wire_added", self.wire)

    def undo(self):
        """Undo the wire addition command and emit 'remove' event."""
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        if self.wire in harness.wires:
            harness.wires.remove(self.wire)
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "remove", "item": self.wire})
        else:
            self.api.dispatch("model_changed", {"action": "remove", "item": self.wire})
        self.api.dispatch("wire_removed", self.wire)

class AddPinCommand(BaseCommand):
    """Command to add a pin to the harness, supporting undo/redo."""
    def __init__(self, pin_or_device, context=None, **kwargs):
        """Initialize AddPinCommand with pin or device and context."""
        BaseCommand.__init__(self, "Add Pin")
        if hasattr(pin_or_device, 'pins'):
            self.device = pin_or_device
            self.pin = Pin(id=str(uuid.uuid4()), x=0, y=0, device_id=self.device.id)
        else:
            self.device = None
            self.pin = pin_or_device
        self.context = context
        self.api = APIManager.get_instance()
        self.new_pos = kwargs.get('new_pos', None)
        self.old_pos = kwargs.get('old_pos', None)

    def execute(self):
        """Add the pin to the device or harness and dispatch event."""
        if self.device:
            if self.pin not in self.device.pins:
                self.device.pins.append(self.pin)
        elif hasattr(self.api.context.harness, 'pins'):
            if self.pin not in self.api.context.harness.pins:
                self.api.context.harness.pins.append(self.pin)
        self.api.dispatch("model_changed", {"action": "add", "item": self.pin})

    def undo(self):
        """Remove the pin from the device or harness and dispatch event."""
        if self.device:
            if self.pin in self.device.pins:
                self.device.pins.remove(self.pin)
        elif hasattr(self.api.context.harness, 'pins'):
            if self.pin in self.api.context.harness.pins:
                self.api.context.harness.pins.remove(self.pin)
        self.api.dispatch("model_changed", {"action": "remove", "item": self.pin})

class DeletePinCommand(BaseCommand):
    """Command to delete a pin from the harness, supporting undo/redo."""
    def __init__(self, pin_or_device, pin=None, context=None, **kwargs):
        """Initialize DeletePinCommand with pin or device and context."""
        BaseCommand.__init__(self, "Delete Pin")
        if hasattr(pin_or_device, 'pins'):
            self.device = pin_or_device
            self.pin = pin if pin is not None else kwargs.get('pin')
        else:
            self.device = None
            self.pin = pin_or_device
        self.context = context
        self.api = APIManager.get_instance()
        self.new_pos = kwargs.get('new_pos', None)
        self._saved_internal_routing = None
        self._saved_pins = None
        self._saved_pin_routing = None


    def execute(self):
        """Remove the pin from the device or harness by id and dispatch event. Also remove from internal_routing if present."""
        if self.device:
            # Save internal_routing and pins for undo
            if hasattr(self.device, 'internal_routing') and hasattr(self.pin, 'id'):
                self._saved_internal_routing = dict(self.device.internal_routing)
                # Save only the routing entries for this pin (both as key and as value)
                self._saved_pin_routing = {
                    self.pin.id: self.device.internal_routing.get(self.pin.id)
                }
                for k, v in self.device.internal_routing.items():
                    if v == self.pin.id:
                        self._saved_pin_routing[k] = v
            self._saved_pins = list(self.device.pins)
            # Remove by id, not by object identity
            self.device.pins = [p for p in self.device.pins if getattr(p, 'id', None) != getattr(self.pin, 'id', None)]
            if hasattr(self.device, 'internal_routing') and hasattr(self.pin, 'id'):
                self.device.internal_routing.pop(self.pin.id, None)
                to_remove = [k for k, v in self.device.internal_routing.items() if v == self.pin.id]
                for k in to_remove:
                    self.device.internal_routing.pop(k, None)
        elif hasattr(self.api.context.harness, 'pins'):
            self._saved_pins = list(self.api.context.harness.pins)
            self.api.context.harness.pins = [p for p in self.api.context.harness.pins if getattr(p, 'id', None) != getattr(self.pin, 'id', None)]
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "remove", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "remove", "item": self.pin})


    def undo(self):
        """Restore the pin list and internal_routing to their saved state and dispatch event."""
        if self.device:
            if self._saved_pins is not None:
                self.device.pins = list(self._saved_pins)
            if hasattr(self.device, 'internal_routing') and self._saved_internal_routing is not None:
                self.device.internal_routing.clear()
                self.device.internal_routing.update(self._saved_internal_routing)
        elif hasattr(self.api.context.harness, 'pins'):
            if self._saved_pins is not None:
                self.api.context.harness.pins = list(self._saved_pins)
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "add", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "add", "item": self.pin})


class DeleteDeviceCommand(BaseCommand):
    """Command to delete a device from the harness, supporting undo/redo."""
    def __init__(self, device, context=None):
        """Initialize DeleteDeviceCommand with device and optional context."""
        BaseCommand.__init__(self, "Delete Device")
        self.device = device
        self.context = context
        self.api = APIManager.get_instance()

    def execute(self):
        """Remove the device from the harness and dispatch event."""
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        with DeviceList.test_bypass():
            if self.device in harness.devices:
                harness.devices.remove(self.device)
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "delete", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "delete", "item": self.device})
        self.api.dispatch("device_removed", self.device)

    def undo(self):
        """Add the device back to the harness and dispatch event."""
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        with DeviceList.test_bypass():
            if self.device not in harness.devices:
                harness.devices.append(self.device)
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "add", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "add", "item": self.device})
        self.api.dispatch("device_added", self.device)

class MoveDeviceCommand(BaseCommand):
    """Command to move a device to a new position, supporting undo/redo."""
    def __init__(self, device, old_pos, new_pos, context=None):
        """Initialize MoveDeviceCommand with device, old and new positions, and optional context."""
        BaseCommand.__init__(self, "Move Device")
        self.device = device
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.context = context
        self.api = APIManager.get_instance()

    def execute(self):
        """Move the device to the new position and dispatch event."""
        self.device.x, self.device.y = self.new_pos
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "move", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "move", "item": self.device})

    def undo(self):
        """Move the device back to the old position and dispatch event."""
        self.device.x, self.device.y = self.old_pos
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "move", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "move", "item": self.device})

# --- Actions ---

@register_action("device.add_pin")
def device_add_pin(context):
    """Add a pin to the selected device using the AddPinCommand."""
    mgr = SelectionManager()
    selection = mgr.selected_models
    if not selection:
        return

    devices = [item for item in selection if hasattr(item, 'pins')]
    if not devices:
        return

    target = devices[0]
    cmd = AddPinCommand(target)
    APIManager.get_instance().context.undo_stack.push(cmd)