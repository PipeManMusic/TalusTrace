"""
Edit and Delete Command Implementations for Talus Trace

This module defines command classes and dispatcher registrations for edit, add, update, and delete actions
on devices, pins, and other scene items. It supports undo/redo and contract enforcement for the application.
"""
from api.actions import register_action
from api.manager import APIManager
from infra.undo_stack import BaseCommand
from core.selection import SelectionManager
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.theme_dialog import ThemeDialog


# Dispatcher contract: add action (calls APIManager.add_device or add_pin)
@register_action("edit.add")
def edit_add(context):
    """Dispatcher contract: add action (calls APIManager.add_device or add_pin)."""
    from infra.logging import infra_log
    api = APIManager.get_instance()
    if hasattr(context, 'device'):
        infra_log(f"[DISPATCHER] edit.add: context.device id={getattr(context.device, 'id', None)}, obj={context.device}", level="debug")
        api.add_device(context.device)
    elif hasattr(context, 'pin'):
        infra_log(f"[DISPATCHER] edit.add: context.pin id={getattr(context.pin, 'id', None)}, obj={context.pin}", level="debug")
        api.add_pin(context.pin)
    else:
        infra_log(f"[DISPATCHER] edit.add: context has neither device nor pin. Context: {context}", level="debug")

# Dispatcher contract: update action (no-op for now)
@register_action("edit.update")
def edit_update(context):
    """Stub for dispatcher contract: update action (no-op)."""
    pass
"""
Edit command implementations for property updates, item deletion, and rotation in Talus Trace.
Provides undoable command classes for editing model objects and dispatching changes.
"""

from api.actions import register_action
from api.manager import APIManager
from infra.undo_stack import BaseCommand
from core.selection import SelectionManager
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.theme_dialog import ThemeDialog

# --- Command Classes ---

class UpdatePropertyCommand(BaseCommand):
    """
    Command to update a property on a target object, supporting undo/redo.
    """
    def __init__(self, target, field, new_value):
        """
        Initialize the command with target object, field name, and new value.
        """
        super().__init__(f"Update {field}")
        self.target = target
        self.field = field
        self.new_value = new_value
        self.is_dict = isinstance(target, dict)
        # For meta fields, track if the key existed before
        if isinstance(field, str) and field.startswith('meta.') and hasattr(target, 'meta') and isinstance(target.meta, dict):
            meta_key = field.split('.', 1)[1]
            self._meta_key_existed = meta_key in target.meta
            self.old_value = target.meta.get(meta_key)
        else:
            self.old_value = target.get(field) if self.is_dict else getattr(target, field, None)
        self.api = APIManager.get_instance()

    def execute(self):
        """Execute the property update on the target object."""
        if self.is_dict:
            self.target[self.field] = self.new_value
        elif isinstance(self.field, str) and self.field.startswith('meta.'):
            meta_key = self.field.split('.', 1)[1]
            if hasattr(self.target, 'meta') and isinstance(self.target.meta, dict):
                self.target.meta[meta_key] = self.new_value
        else:
            setattr(self.target, self.field, self.new_value)
        self.api.dispatch("model_changed", {"action": "update", "item": self.target})

    def undo(self):
        """Undo the property update, restoring the old value or removing the key if it did not exist before."""
        if self.is_dict:
            self.target[self.field] = self.old_value
        elif isinstance(self.field, str) and self.field.startswith('meta.'):
            meta_key = self.field.split('.', 1)[1]
            if hasattr(self.target, 'meta') and isinstance(self.target.meta, dict):
                if hasattr(self, '_meta_key_existed') and not self._meta_key_existed:
                    # Key did not exist before, so remove it
                    self.target.meta.pop(meta_key, None)
                else:
                    self.target.meta[meta_key] = self.old_value
        else:
            setattr(self.target, self.field, self.old_value)
        self.api.dispatch("model_changed", {"action": "update", "item": self.target})

class DeleteItemsCommand(BaseCommand):
    """
    Command to delete devices and wires from the model, supporting undo/redo.
    """
    def __init__(self, device_ids, wire_ids):
        """
        Initialize the command with device and wire IDs to delete.
        """
        super().__init__("Delete Items")
        # Accept both Device objects and IDs
        self.dev_ids = [d.id if hasattr(d, 'id') else d for d in device_ids]
        self.wire_ids = [w.id if hasattr(w, 'id') else w for w in wire_ids]
        self.api = APIManager.get_instance()
        # Capture state for undo
        self.deleted_devices = []
        self.deleted_wires = []

    def execute(self):
        """Delete the specified devices and wires from the model."""
        harness = self.api.context.harness
        # Save for undo
        self.deleted_devices = [d for d in harness.devices if d.id in self.dev_ids]
        self.deleted_wires = [w for w in harness.wires if getattr(w, 'id', None) in self.wire_ids]
        # Dispatch 'remove' for each deleted device and wire (API contract) BEFORE mutation
        for device in self.deleted_devices:
            self.api.dispatch("model_changed", {"action": "remove", "item": device, "type": "device"})
            self.api.dispatch("device_removed", device)
        for wire in self.deleted_wires:
            self.api.dispatch("model_changed", {"action": "remove", "item": wire, "type": "wire"})
            self.api.dispatch("wire_removed", wire)
        # Mutate after dispatch: remove devices and their pins
        harness.devices = [d for d in harness.devices if d.id not in self.dev_ids]
        # (Pins are contained in device, so removing device removes pins)
        harness.wires = [w for w in harness.wires if getattr(w, 'id', None) not in self.wire_ids]
        SelectionManager().clear_selection()

    def undo(self):
        """Restore the deleted devices and wires to the model."""
        harness = self.api.context.harness
        # Dispatch 'restore' for each restored device and wire (API contract) BEFORE mutation
        for device in self.deleted_devices:
            self.api.dispatch("model_changed", {"action": "restore", "item": device, "type": "device"})
            self.api.dispatch("device_restored", device)
        for wire in self.deleted_wires:
            self.api.dispatch("model_changed", {"action": "restore", "item": wire, "type": "wire"})
            self.api.dispatch("wire_restored", wire)
        # Restore devices and their pins
        for device in self.deleted_devices:
            if all(d.id != device.id for d in harness.devices):
                harness.devices.append(device)
        for wire in self.deleted_wires:
            if all(w.id != wire.id for w in harness.wires):
                harness.wires.append(wire)

class RotateItemsCommand(BaseCommand):
    """
    Command to rotate items by a specified angle, supporting undo/redo.
    """
    def __init__(self, items, angle):
        """
        Initialize the command with item IDs and rotation angle.
        """
        super().__init__("Rotate Items")
        self.items = items
        self.angle = angle
        self.api = APIManager.get_instance()

    def execute(self):
        """Rotate the items by the specified angle."""
        for item in self.items:
            if hasattr(item, 'rotation'):
                item.rotation = (item.rotation + self.angle) % 360
                self.api.dispatch("model_changed", {"action": "update", "item": item})

    def undo(self):
        """Undo the rotation, restoring the previous angle."""
        for item in self.items:
            if hasattr(item, 'rotation'):
                item.rotation = (item.rotation - self.angle) % 360
                self.api.dispatch("model_changed", {"action": "update", "item": item})

# --- Action Registrations ---

@register_action("edit.undo")
def edit_undo(context):
    """Undo the last command using the undo stack."""
    APIManager.get_instance().context.undo_stack.undo()

@register_action("edit.redo")
def edit_redo(context):
    """Redo the last undone command using the undo stack."""
    APIManager.get_instance().context.undo_stack.redo()

@register_action("edit.delete")
def edit_delete(context):
    """Dispatcher contract: delete action (calls APIManager.delete_device, delete_pin, or delete_wire)."""
    from infra.logging import infra_log
    api = APIManager.get_instance()
    from api.commands.device import DeletePinCommand
    infra_log(f"[DISPATCHER] edit.delete called with context: {context}", level="info")
    if hasattr(context, 'pin'):
        pin = context.pin
        # Always resolve device from pin.device_id
        device = getattr(context, 'device', None)
        if device is None and hasattr(pin, 'device_id'):
            device = next((d for d in api.context.harness.devices if getattr(d, 'id', None) == getattr(pin, 'device_id', None)), None)
        # Always use the canonical pin instance from device.pins if possible
        canonical_pin = None
        if device is not None and hasattr(device, 'pins'):
            canonical_pin = next((p for p in device.pins if getattr(p, 'id', None) == getattr(pin, 'id', None)), None)
        if canonical_pin is not None:
            pin = canonical_pin
        if device is not None:
            infra_log(f"[DISPATCHER] edit.delete: pushing DeletePinCommand with device id={getattr(device, 'id', None)}, pin id={getattr(pin, 'id', None)}", level="info")
            api.context.undo_stack.push(DeletePinCommand(device, pin, context=api.context))
        else:
            api.delete_pin(pin)
    elif hasattr(context, 'device'):
        infra_log(f"[DISPATCHER] edit.delete: context.device id={getattr(context.device, 'id', None)}", level="debug")
        api.delete_device(context.device)
    elif hasattr(context, 'wire'):
        infra_log(f"[DISPATCHER] edit.delete: context.wire id={getattr(context.wire, 'id', None)}", level="debug")
        api.delete_wire(context.wire)
    else:
        infra_log(f"[DISPATCHER] edit.delete: no pin/device/wire on context, falling back to selection", level="debug")
        mgr = SelectionManager()
        for item in mgr.selected_models:
            if hasattr(item, 'meta') and hasattr(item, 'pins'):
                infra_log(f"[DISPATCHER] edit.delete: fallback device id={getattr(item, 'id', None)}", level="debug")
                api.delete_device(item)
            elif hasattr(item, 'device_id') and hasattr(item, 'id'):
                infra_log(f"[DISPATCHER] edit.delete: fallback pin id={getattr(item, 'id', None)}", level="debug")
                device = next((d for d in api.context.harness.devices if getattr(d, 'id', None) == getattr(item, 'device_id', None)), None)
                if device is not None:
                    api.context.undo_stack.push(DeletePinCommand(device, item, context=api.context))
                else:
                    api.delete_pin(item)
            elif hasattr(item, 'path_nodes'):
                infra_log(f"[DISPATCHER] edit.delete: fallback wire id={getattr(item, 'id', None)}", level="debug")
                api.delete_wire(item)

# --- PinDeleteCommand ---
class PinDeleteCommand(BaseCommand):
    """
    Command to delete one or more pins from their parent devices, supporting undo/redo.
    """
    def __init__(self, pin_tuples):
        """
        Initialize the PinDeleteCommand.
        Args:
            pin_tuples (list): List of (device, pin) tuples to delete.
        """
        super().__init__("Delete Pin(s)")
        self.pin_tuples = pin_tuples  # List of (device, pin)
        self.api = APIManager.get_instance()
        self._removed = []  # For undo: (device, pin, idx)

    def execute(self):
        """
        Remove pins from their parent devices and dispatch model_changed events.
        """
        for device, pin in self.pin_tuples:
            if pin in device.pins:
                idx = device.pins.index(pin)
                device.pins.remove(pin)
                self._removed.append((device, pin, idx))
                self.api.dispatch("model_changed", {"action": "remove", "item": pin, "type": "pin"})
        SelectionManager().clear_selection()

    def undo(self):
        """
        Restore pins to their parent devices at their original indices and dispatch model_changed events.
        """
        for device, pin, idx in reversed(self._removed):
            if pin not in device.pins:
                device.pins.insert(idx, pin)
                self.api.dispatch("model_changed", {"action": "restore", "item": pin, "type": "pin"})

@register_action("edit.rotate_cw")
def edit_rotate_cw(context):
    """Rotate selected items clockwise by 90 degrees."""
    mgr = SelectionManager()
    if not mgr.selected_models: return
    cmd = RotateItemsCommand(mgr.selected_models, 90)
    APIManager.get_instance().context.undo_stack.push(cmd)

@register_action("edit.rotate_ccw")
def edit_rotate_ccw(context):
    """Rotate selected items counterclockwise by 90 degrees."""
    mgr = SelectionManager()
    if not mgr.selected_models: return
    cmd = RotateItemsCommand(mgr.selected_models, -90)
    APIManager.get_instance().context.undo_stack.push(cmd)

@register_action("edit.update_property")
def edit_update_property(context):
    """Update a property on a model object. Invoked programmatically by PropertyPanel."""
    pass # Invoked programmatically by PropertyPanel

@register_action("edit.settings")
def edit_settings(context):
    """Open the settings dialog, modal to the main window."""
    # Pass main_window as parent if available to make dialog modal
    mw = APIManager.get_instance().main_window
    dlg = SettingsDialog(mw)
    import sys
    if 'pytest' in sys.modules:
        dlg.accept()  # Auto-close for tests
    else:
        dlg.exec_()

@register_action("edit.theme")
def edit_theme(context):
    """Open the theme selection dialog."""
    mw = APIManager.get_instance().main_window
    dlg = ThemeDialog(mw)
    import sys
    if 'pytest' in sys.modules:
        dlg.accept()  # Auto-close for tests
    else:
        dlg.exec_()
