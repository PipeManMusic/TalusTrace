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
        self.old_value = target.get(field) if self.is_dict else getattr(target, field, None)
        self.api = APIManager.get_instance()

    def execute(self):
        """Execute the property update on the target object."""
        if self.is_dict: self.target[self.field] = self.new_value
        else: setattr(self.target, self.field, self.new_value)
        self.api.dispatch("model_changed", {"action": "update", "item": self.target})

    def undo(self):
        """Undo the property update, restoring the old value."""
        if self.is_dict: self.target[self.field] = self.old_value
        else: setattr(self.target, self.field, self.old_value)
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
        print(f"[DEBUG] DeleteItemsCommand.execute: harness.devices before {[d.id for d in self.api.context.harness.devices]}")
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
        print(f"[DEBUG] DeleteItemsCommand.execute: harness.devices after {[d.id for d in harness.devices]}")
        # (Pins are contained in device, so removing device removes pins)
        harness.wires = [w for w in harness.wires if getattr(w, 'id', None) not in self.wire_ids]
        SelectionManager().clear_selection()

    def undo(self):
        """Restore the deleted devices and wires to the model."""
        harness = self.api.context.harness
        print(f"[DEBUG] DeleteItemsCommand.undo: harness.devices before {[d.id for d in harness.devices]}")
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
        print(f"[DEBUG] DeleteItemsCommand.undo: harness.devices after {[d.id for d in harness.devices]}")
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
        self.api.dispatch("model_changed", {"action": "rotate"})

    def undo(self):
        """Undo the rotation, restoring the previous angle."""
        for item in self.items:
            if hasattr(item, 'rotation'):
                item.rotation = (item.rotation - self.angle) % 360
        self.api.dispatch("model_changed", {"action": "rotate"})

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
    """Delete selected devices and wires, with confirmation for connected wires."""
    mgr = SelectionManager()
    if not mgr.current_selection_ids: return
    
    # Identify what to delete
    dev_ids = []
    wire_ids = []

    # Collect device and wire IDs from selection
    for item in mgr.selected_models:
        # Device: must have 'meta' and 'pins'
        if hasattr(item, 'meta') and hasattr(item, 'pins'):
            dev_ids.append(item.id)
        # Wire: must have 'from_conn' and 'to_conn'
        elif hasattr(item, 'from_conn') and hasattr(item, 'to_conn'):
            wire_ids.append(item.id)

    # If deleting a device, also delete all connected wires
    if dev_ids:
        api = APIManager.get_instance()
        harness = api.context.harness
        connected_wire_ids = []
        for wire in harness.wires:
            if wire.from_conn in dev_ids or wire.to_conn in dev_ids:
                connected_wire_ids.append(wire.id)
        # If there are connected wires, show confirmation dialog
        if connected_wire_ids:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Deleting device(s) will also delete connected wires.")
            msg.setInformativeText(f"Device IDs: {dev_ids}\nConnected Wire IDs: {connected_wire_ids}\nContinue?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            ret = msg.exec_()
            if ret != QMessageBox.Yes:
                return  # Abort deletion
        wire_ids.extend(connected_wire_ids)

    cmd = DeleteItemsCommand(dev_ids, wire_ids)
    APIManager.get_instance().context.undo_stack.push(cmd)

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
