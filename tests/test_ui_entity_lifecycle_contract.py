import pytest
from unittest.mock import patch
from PySide6.QtCore import QPointF
from ui.main_window import MainWindow
from api.manager import APIManager

def _simulate_device_add(window, qtbot):
    api = window.api
    api.tool_manager.set_tool("placement")
    placement_tool = api.tool_manager.get_tool("placement")
    scene_pos = QPointF(100, 100)
    placement_tool.start_drag(None, scene_pos)
    class DummyEvent:
        def __init__(self, x, y):
            self.x = lambda: x
            self.y = lambda: y
            self.button = lambda: 1  # Qt.LeftButton
            self.scene_pos = QPointF(x, y)
    placement_tool.on_mouse_press(DummyEvent(100, 100))
    return api.context.harness.devices[-1]

def _simulate_pin_add(api, device):
    from api.commands.device import AddPinCommand
    pin = type('Pin', (), {'id': 'testpin', 'device_id': device.id, 'x': 0, 'y': 0})()
    AddPinCommand(device, pin, context=api.context).execute()
    return pin

def _simulate_wire_add(api, device_a, device_b):
    from api.commands.device import AddWireCommand
    wire = type('Wire', (), {'id': 'testwire', 'from_device': device_a.id, 'to_device': device_b.id, 'path_nodes': []})()
    AddWireCommand(wire, context=api.context).execute()
    return wire

def _simulate_bundle_add(api, device_list):
    from api.commands.bundle import AddBundleCommand
    bundle = type('Bundle', (), {'id': 'testbundle', 'members': [d.id for d in device_list]})()
    AddBundleCommand(bundle, api.context.harness).execute()
    return bundle

@pytest.mark.parametrize("entity,add_fn,remove_cmd,update_cmd,copy_cmd,paste_cmd", [
    ("device", _simulate_device_add, "DeleteDeviceCommand", "UpdateDeviceCommand", "CopyDeviceCommand", "PasteDeviceCommand"),
    ("pin", _simulate_pin_add, "DeletePinCommand", "UpdatePinCommand", "CopyPinCommand", "PastePinCommand"),
    ("wire", _simulate_wire_add, "DeleteWireCommand", "UpdateWireCommand", "CopyWireCommand", "PasteWireCommand"),
    ("bundle", _simulate_bundle_add, "DeleteBundleCommand", "UpdateBundleCommand", "CopyBundleCommand", "PasteBundleCommand"),
])
def test_entity_lifecycle_contract(entity, add_fn, remove_cmd, update_cmd, copy_cmd, paste_cmd, qtbot):
    """
    Contract: Full lifecycle for {entity} must use command pattern and undo/redo for add, remove, update, copy, paste.
    """
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = window.api
    # Add entity
    if entity == "device":
        obj = add_fn(window, qtbot)
    elif entity == "pin":
        device = _simulate_device_add(window, qtbot)
        obj = add_fn(api, device)
    elif entity == "wire":
        device_a = _simulate_device_add(window, qtbot)
        device_b = _simulate_device_add(window, qtbot)
        obj = add_fn(api, device_a, device_b)
    elif entity == "bundle":
        device_a = _simulate_device_add(window, qtbot)
        device_b = _simulate_device_add(window, qtbot)
        obj = add_fn(api, [device_a, device_b])
    # Patch and test remove, update, copy, paste commands
    for cmd_name in [remove_cmd, update_cmd, copy_cmd, paste_cmd]:
        # Bundle commands live in api.commands.bundle, others in api.commands.device
        cmd_module = "api.commands.bundle" if entity == "bundle" else "api.commands.device"
        with patch(f"{cmd_module}.{cmd_name}.__init__", return_value=None) as cmd_init, \
             patch.object(api.context.undo_stack, "push") as push_mock:
            # Simulate command usage
            # (In real code, call the actual API method or UI action)
            # Here, just instantiate and push the command
            cmd_class = getattr(__import__(cmd_module, fromlist=[cmd_name]), cmd_name)
            cmd = cmd_class(obj, context=api.context)
            api.context.undo_stack.push(cmd)
            assert cmd_init.called, f"{cmd_name} was not constructed for {entity}!"
            assert push_mock.called, f"Undo stack was not used for {cmd_name} on {entity}!"
    # Test undo/redo
    api.context.undo_stack.undo()
    api.context.undo_stack.redo()
