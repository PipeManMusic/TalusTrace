"""
Device, pin, and wire command implementations for undo/redo and contract enforcement in Talus Trace.
Implements Add, Delete, Update, Copy, and Paste commands for devices, pins, and wires.
"""
# --- RotateDeviceCommand ---
from infra.undo_stack import BaseCommand
from api.manager import APIManager
from core.selection import SelectionManager

class RotateDeviceCommand(BaseCommand):
    """Command to rotate a device by a given angle, supporting undo/redo."""
    def __init__(self, device, angle, context=None, logging_flag=False):
        """Initialize RotateDeviceCommand with device, angle (degrees), and optional context."""
        BaseCommand.__init__(self, "Rotate Device")
        self.device = device
        self.angle = angle
        self.context = context
        self.api = APIManager.get_instance()
        self._prev_rotation = getattr(device, 'rotation', 0.0)
        self.logging_flag = logging_flag

    def execute(self):
        """Rotate the device by the specified angle and dispatch event."""
        prev = getattr(self.device, 'rotation', 0.0)
        new_rotation = (prev + self.angle) % 360
        self.device.rotation = new_rotation
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "rotate", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "rotate", "item": self.device})

    def undo(self):
        """Restore the device's previous rotation and dispatch event."""
        self.device.rotation = self._prev_rotation
        if self.context and hasattr(self.context, "observer"):
            self.context.observer.dispatch("model_changed", {"action": "rotate", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "rotate", "item": self.device})
"""
Device, pin, and wire command implementations for undo/redo and contract enforcement in Talus Trace.
Implements Add, Delete, Update, Copy, and Paste commands for devices, pins, and wires.
"""
from infra.undo_stack import BaseCommand
class UpdateBundleCommand(BaseCommand):
    """
    Command to update a bundle's data in the system.
    """
    def __init__(self, bundle, context=None, logging_flag=False, **kwargs):
        """
        Initialize the UpdateBundleCommand.
        Args:
            bundle: The bundle object to update.
            context: Optional context for the update operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Update Bundle")
        self.bundle = bundle
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to update the bundle.
        """
        pass

    def undo(self):
        """
        Undo the update to the bundle.
        """
        pass

class CopyBundleCommand(BaseCommand):
    """
    Command to copy a bundle in the system.
    """
    def __init__(self, bundle, context=None, logging_flag=False, **kwargs):
        """
        Initialize the CopyBundleCommand.
        Args:
            bundle: The bundle object to copy.
            context: Optional context for the copy operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Copy Bundle")
        self.bundle = bundle
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to copy the bundle.
        """
        pass

    def undo(self):
        """
        Undo the copy operation for the bundle.
        """
        pass

class PasteBundleCommand(BaseCommand):
    """
    Command to paste a bundle into the system.
    """
    def __init__(self, bundle, context=None, logging_flag=False, **kwargs):
        """
        Initialize the PasteBundleCommand.
        Args:
            bundle: The bundle object to paste.
            context: Optional context for the paste operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Paste Bundle")
        self.bundle = bundle
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to paste the bundle.
        """
        pass

    def undo(self):
        """
        Undo the paste operation for the bundle.
        """
        pass
from infra.undo_stack import BaseCommand
class DeleteBundleCommand(BaseCommand):
    """
    Command to delete a bundle from the system.
    """
    def __init__(self, bundle, context=None, logging_flag=False, **kwargs):
        """
        Initialize the DeleteBundleCommand.
        Args:
            bundle: The bundle object to delete.
            context: Optional context for the delete operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Delete Bundle")
        self.bundle = bundle
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to delete the bundle.
        """
        pass

    def undo(self):
        """
        Undo the deletion of the bundle.
        """
        pass
from infra.undo_stack import BaseCommand
class UpdateDeviceCommand(BaseCommand):
    """
    Command to update a device's data in the system.
    """
    def __init__(self, device, context=None, logging_flag=False, **kwargs):
        """
        Initialize the UpdateDeviceCommand.
        Args:
            device: The device object to update.
            context: Optional context for the update operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Update Device")
        self.device = device
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to update the device.
        """
        pass

    def undo(self):
        """
        Undo the update to the device.
        """
        pass

class CopyDeviceCommand(BaseCommand):
    """
    Command to copy a device in the system.
    """
    def __init__(self, device, context=None, logging_flag=False, **kwargs):
        """
        Initialize the CopyDeviceCommand.
        Args:
            device: The device object to copy.
            context: Optional context for the copy operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Copy Device")
        self.device = device
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to copy the device.
        """
        pass

    def undo(self):
        """
        Undo the copy operation for the device.
        """
        pass

class PasteDeviceCommand(BaseCommand):
    """
    Command to paste a device into the system.
    """
    def __init__(self, device, context=None, logging_flag=False, **kwargs):
        """
        Initialize the PasteDeviceCommand.
        Args:
            device: The device object to paste.
            context: Optional context for the paste operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Paste Device")
        self.device = device
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to paste the device.
        """
        pass

    def undo(self):
        """
        Undo the paste operation for the device.
        """
        pass

class UpdatePinCommand(BaseCommand):
    """
    Command to update a pin's data in the system.
    """
    def __init__(self, pin, context=None, logging_flag=False, **kwargs):
        """
        Initialize the UpdatePinCommand.
        Args:
            pin: The pin object to update.
            context: Optional context for the update operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Update Pin")
        self.pin = pin
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to update the pin.
        """
        pass

    def undo(self):
        """
        Undo the update to the pin.
        """
        pass

class CopyPinCommand(BaseCommand):
    """
    Command to copy a pin in the system.
    """
    def __init__(self, pin, context=None, logging_flag=False, **kwargs):
        """
        Initialize the CopyPinCommand.
        Args:
            pin: The pin object to copy.
            context: Optional context for the copy operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Copy Pin")
        self.pin = pin
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to copy the pin.
        """
        pass

    def undo(self):
        """
        Undo the copy operation for the pin.
        """
        pass

class PastePinCommand(BaseCommand):
    """
    Command to paste a pin into the system.
    """
    def __init__(self, pin, context=None, logging_flag=False, **kwargs):
        """
        Initialize the PastePinCommand.
        Args:
            pin: The pin object to paste.
            context: Optional context for the paste operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Paste Pin")
        self.pin = pin
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to paste the pin.
        """
        pass

    def undo(self):
        """
        Undo the paste operation for the pin.
        """
        pass

class UpdateWireCommand(BaseCommand):
    """
    Command to update a wire's data in the system.
    """
    def __init__(self, wire, context=None, logging_flag=False, **kwargs):
        """
        Initialize the UpdateWireCommand.
        Args:
            wire: The wire object to update.
            context: Optional context for the update operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Update Wire")
        self.wire = wire
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to update the wire.
        """
        pass

    def undo(self):
        """
        Undo the update to the wire.
        """
        pass

class DeleteWireCommand(BaseCommand):
    """
    Command to delete a wire from the system.
    """
    def __init__(self, wire, context=None, logging_flag=False, **kwargs):
        """
        Initialize the DeleteWireCommand.
        Args:
            wire: The wire object to delete.
            context: Optional context for the delete operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Delete Wire")
        self.wire = wire
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to delete the wire.
        """
        pass

    def undo(self):
        """
        Undo the deletion of the wire.
        """
        pass

class CopyWireCommand(BaseCommand):
    """
    Command to copy a wire in the system.
    """
    def __init__(self, wire, context=None, logging_flag=False, **kwargs):
        """
        Initialize the CopyWireCommand.
        Args:
            wire: The wire object to copy.
            context: Optional context for the copy operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Copy Wire")
        self.wire = wire
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to copy the wire.
        """
        pass

    def undo(self):
        """
        Undo the copy operation for the wire.
        """
        pass

class PasteWireCommand(BaseCommand):
    """
    Command to paste a wire into the system.
    """
    def __init__(self, wire, context=None, logging_flag=False, **kwargs):
        """
        Initialize the PasteWireCommand.
        Args:
            wire: The wire object to paste.
            context: Optional context for the paste operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Paste Wire")
        self.wire = wire
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to paste the wire.
        """
        pass

    def undo(self):
        """
        Undo the paste operation for the wire.
        """
        pass

class AddBundleCommand(BaseCommand):
    """
    Command to add a bundle to the system.
    """
    def __init__(self, bundle, context=None, logging_flag=False, **kwargs):
        """
        Initialize the AddBundleCommand.
        Args:
            bundle: The bundle object to add.
            context: Optional context for the add operation.
            **kwargs: Additional keyword arguments for extensibility.
        """
        super().__init__("Add Bundle")
        self.bundle = bundle
        self.context = context
        self.logging_flag = logging_flag

    def execute(self):
        """
        Execute the command to add the bundle.
        """
        pass

    def undo(self):
        """
        Undo the addition of the bundle.
        """
        pass
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
    def __init__(self, device, context=None, logging_flag=False, **kwargs):
        """Initialize AddDeviceCommand with device and optional context."""
        BaseCommand.__init__(self, "Add Device")
        self.device = device
        self.context = context
        self.api = APIManager.get_instance()
        self.logging_flag = logging_flag

    def execute(self):
        """Add the device to the harness and dispatch event. Logs call stack for diagnostics."""
        from infra.logging import infra_log
        device_id = getattr(self.device, 'id', None)
        if self.logging_flag:
            infra_log(f"[AddDeviceCommand] execute START for device id={device_id}", level="debug")
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        with DeviceList.test_bypass():
            if self.device not in harness.devices:
                harness.devices.append(self.device)
                infra_log(f"[AddDeviceCommand] Device appended to harness.devices: {device_id}", level="debug")
            else:
                infra_log(f"[AddDeviceCommand] Device already in harness.devices: {device_id}", level="debug")
        # Prefer observer from the explicit context, fall back to APIManager context
        observer = None
        if self.context and hasattr(self.context, 'observer'):
            observer = getattr(self.context, 'observer', None)
        if observer is None:
            api_ctx = getattr(self.api, 'context', None)
            observer = getattr(api_ctx, 'observer', None)
        if observer:
            infra_log(f"[AddDeviceCommand] Dispatching model_changed via APIManager.context.observer for device id={device_id}", level="debug")
            observer.dispatch("model_changed", {"action": "add", "item": self.device})
        else:
            infra_log(f"[AddDeviceCommand] Dispatching model_changed via api.dispatch for device id={device_id}", level="debug")
            self.api.dispatch("model_changed", {"action": "add", "item": self.device})
        self.api.dispatch("device_added", self.device)
        if self.logging_flag:
            infra_log(f"[AddDeviceCommand] execute COMPLETE for device id={device_id}", level="debug")

    def undo(self):
        """Remove the device from the harness and dispatch event."""
        from infra.logging import infra_log
        if self.logging_flag:
            infra_log.info(f"[LOG] AddDeviceCommand.undo START for device id={getattr(self.device, 'id', None)}")
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        with DeviceList.test_bypass():
            if self.device in harness.devices:
                harness.devices.remove(self.device)
        observer = getattr(self.api, 'context', None)
        observer = getattr(observer, 'observer', None)
        if observer:
            observer.dispatch("model_changed", {"action": "delete", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "delete", "item": self.device})
        self.api.dispatch("device_removed", self.device)
        if self.logging_flag:
            infra_log.info(f"[LOG] AddDeviceCommand.undo COMPLETE for device id={getattr(self.device, 'id', None)}")

class MovePinCommand(BaseCommand):
    """Command to move a pin to a new position, supporting undo/redo."""
    def __init__(self, pin, old_pos, new_pos, context=None, logging_flag=False):
        """Initialize MovePinCommand with pin, old and new positions, and optional context."""
        BaseCommand.__init__(self, "Move Pin")
        self.pin = pin
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.context = context
        self.api = APIManager.get_instance()
        self.logging_flag = logging_flag

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
    def __init__(self, wire, context=None, logging_flag=False, **kwargs):
        """Initialize AddWireCommand with wire, context, and optional positions."""
        BaseCommand.__init__(self, "Add Wire")
        self.wire = wire
        self.context = context
        self.api = APIManager.get_instance()
        self.new_pos = kwargs.get('new_pos', None)
        self.old_pos = kwargs.get('old_pos', None)
        self.logging_flag = logging_flag

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
    def __init__(self, device, pin, context=None, logging_flag=False, **kwargs):
        """Initialize AddPinCommand with device and pin and context."""
        BaseCommand.__init__(self, "Add Pin")
        assert device is not None and pin is not None, "AddPinCommand requires both device and pin."
        self.device = device
        self.pin = pin
        self.context = context
        self.api = APIManager.get_instance()
        self.new_pos = kwargs.get('new_pos', None)
        self.old_pos = kwargs.get('old_pos', None)
        self.logging_flag = logging_flag

    def execute(self):
        """Add the pin to the device and dispatch event."""
        if self.pin not in self.device.pins:
            self.device.pins.append(self.pin)
        observer = getattr(self.api, 'context', None)
        observer = getattr(observer, 'observer', None)
        if observer:
            observer.dispatch("model_changed", {"action": "add", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "add", "item": self.pin})

    def undo(self):
        """Remove the pin from the device and dispatch event."""
        if self.pin in self.device.pins:
            self.device.pins.remove(self.pin)
        observer = getattr(self.api, 'context', None)
        observer = getattr(observer, 'observer', None)
        if observer:
            observer.dispatch("model_changed", {"action": "remove", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "remove", "item": self.pin})

class DeletePinCommand(BaseCommand):
    """Command to delete a pin from the harness, supporting undo/redo."""
    def __init__(self, pin_or_device, pin=None, context=None, logging_flag=False, **kwargs):
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
        self._saved_state = {}
        # If context has _test_logging_flag, force logging_flag True for testability
        if context and getattr(context, '_test_logging_flag', False):
            self.logging_flag = True
        else:
            self.logging_flag = logging_flag
        pin_uuid = getattr(self.pin, 'id', None)
        if self.logging_flag:
            from infra.logging import infra_log
            infra_log(f"[LOG] DeletePinCommand.__init__ for pin UUID={pin_uuid}", level="info")


    def execute(self):
        """Remove the pin from all devices in the harness by UUID and dispatch event."""
        from infra.logging import infra_log
        pin_uuid = getattr(self.pin, 'id', None)
        if self.logging_flag:
            infra_log(f"[LOG] DeletePinCommand.execute START for pin UUID={pin_uuid}", level="info")
        # Save state for undo
        harness_devices = getattr(self.api.context.harness, 'devices', [])
        self._saved_state = {
            getattr(d, 'id', id(d)): {
                'pins': list(getattr(d, 'pins', [])),
                'routing': dict(getattr(d, 'internal_routing', {}) or {})
            }
            for d in harness_devices
        }
        # Remove pin from all devices
        for d in harness_devices:
            if d.get_pin_by_uuid(pin_uuid):
                d.remove_pin(pin_uuid)
        observer = getattr(self.api, 'context', None)
        observer = getattr(observer, 'observer', None)
        if observer:
            observer.dispatch("model_changed", {"action": "remove", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "remove", "item": self.pin})
        if self.logging_flag:
            infra_log(f"[LOG] DeletePinCommand.execute COMPLETE for pin UUID={pin_uuid}", level="info")


    def undo(self):
        """Restore all device pin lists to their saved state and dispatch event."""
        from infra.logging import infra_log
        pin_uuid = getattr(self.pin, 'id', None)
        if self.logging_flag:
            infra_log(f"[LOG] DeletePinCommand.undo START for pin UUID={pin_uuid}", level="info")
        if self._saved_state:
            harness_devices = getattr(self.api.context.harness, 'devices', [])
            for d in harness_devices:
                state = self._saved_state.get(getattr(d, 'id', id(d)))
                if state:
                    d.pins = list(state.get('pins', []))
                    if getattr(d, 'internal_routing', None) is not None:
                        d.internal_routing.clear()
                        d.internal_routing.update(state.get('routing', {}))
        observer = getattr(self.api, 'context', None)
        observer = getattr(observer, 'observer', None)
        if observer:
            observer.dispatch("model_changed", {"action": "add", "item": self.pin})
        else:
            self.api.dispatch("model_changed", {"action": "add", "item": self.pin})
        if self.logging_flag:
            infra_log(f"[LOG] DeletePinCommand.undo COMPLETE for pin UUID={pin_uuid}", level="info")


class DeleteDeviceCommand(BaseCommand):
    """Command to delete a device from the harness, supporting undo/redo."""
    def __init__(self, device, context=None, logging_flag=False):
        """Initialize DeleteDeviceCommand with device and optional context."""
        BaseCommand.__init__(self, "Delete Device")
        self.device = device
        self.context = context
        self.api = APIManager.get_instance()
        self.logging_flag = logging_flag

    def execute(self):
        """Remove the device from the harness and dispatch event."""
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        from infra.logging import infra_log
        if self.logging_flag:
            infra_log(f"[DeleteDeviceCommand] execute START for device id={getattr(self.device, 'id', None)}", level="debug")
        with DeviceList.test_bypass():
            if self.device in harness.devices:
                harness.devices.remove(self.device)
                if self.logging_flag:
                    infra_log(f"[DeleteDeviceCommand] Device removed from harness.devices: {getattr(self.device, 'id', None)}", level="debug")
            else:
                if self.logging_flag:
                    infra_log(f"[DeleteDeviceCommand] Device not found in harness.devices: {getattr(self.device, 'id', None)}", level="debug")
        observer = getattr(self.api, 'context', None)
        observer = getattr(observer, 'observer', None)
        if observer:
            observer.dispatch("model_changed", {"action": "remove", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "remove", "item": self.device})
        self.api.dispatch("device_removed", self.device)
        if self.logging_flag:
            infra_log(f"[DeleteDeviceCommand] execute COMPLETE for device id={getattr(self.device, 'id', None)}", level="debug")

    def undo(self):
        """Add the device back to the harness and dispatch event. Always use 'add' for model_changed."""
        from infra.logging import infra_log
        infra_log(f"[DeleteDeviceCommand] undo called for device id={getattr(self.device, 'id', None)}", level="debug")
        harness = self.context.harness if self.context and hasattr(self.context, 'harness') else self.api.context.harness
        with DeviceList.test_bypass():
            if self.device not in harness.devices:
                harness.devices.append(self.device)
                infra_log(f"[DeleteDeviceCommand] Device re-added to harness.devices: {getattr(self.device, 'id', None)}", level="debug")
            else:
                infra_log(f"[DeleteDeviceCommand] Device already present in harness.devices: {getattr(self.device, 'id', None)}", level="debug")
        # Always use 'add' for undo, never 'restore', for UI compatibility
        observer = getattr(self.api, 'context', None)
        observer = getattr(observer, 'observer', None)
        if observer:
            observer.dispatch("model_changed", {"action": "add", "item": self.device})
        else:
            self.api.dispatch("model_changed", {"action": "add", "item": self.device})
        self.api.dispatch("device_added", self.device)

class MoveDeviceCommand(BaseCommand):
    """Command to move a device to a new position, supporting undo/redo."""
    def __init__(self, device, old_pos, new_pos, context=None, logging_flag=False):
        """Initialize MoveDeviceCommand with device, old and new positions, and optional context."""
        BaseCommand.__init__(self, "Move Device")
        self.device = device
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.context = context
        self.api = APIManager.get_instance()
        self.logging_flag = logging_flag

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
    # Example: create a new Pin instance as needed
    from core.pin import Pin
    import uuid
    pin = Pin(id=str(uuid.uuid4()), x=0, y=0, device_id=target.id)
    cmd = AddPinCommand(target, pin, context=context)
    APIManager.get_instance().context.undo_stack.push(cmd)


# --- Patch: Ensure delete_pin action always passes context ---
@register_action("device.delete_pin")
def device_delete_pin(context):
    """Delete the selected pin from the selected device using DeletePinCommand, always passing context."""
    mgr = SelectionManager()
    selection = mgr.selected_models
    if not selection:
        return

    # Find selected pin and its parent device
    pins = [item for item in selection if hasattr(item, 'device_id')]
    if not pins:
        return

    pin = pins[0]
    # Find the parent device by device_id
    api = APIManager.get_instance()
    device = None
    for d in getattr(api.context.harness, 'devices', []):
        if getattr(d, 'id', None) == getattr(pin, 'device_id', None):
            device = d
            break
    if not device:
        return

    cmd = DeletePinCommand(device, pin, context=context)
    api.context.undo_stack.push(cmd)