import os
import sys
import time
import pytest
from PySide6.QtWidgets import QApplication
from api.manager import APIManager
from ui.main_window import MainWindow

def test_device_removal_updates_canvas(qtbot):
    print("[TEST] Starting device removal UI contract test")
    # Setup app and main window
    app = QApplication.instance() or QApplication(sys.argv)
    api = APIManager.get_instance()
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Add a device using AddDeviceCommand
    from core.models import Device
    import uuid
    from api.commands.device import AddDeviceCommand, DeleteDeviceCommand
    dev_id = str(uuid.uuid4())
    device = Device(id=dev_id, x=0, y=0, meta={})
    add_cmd = AddDeviceCommand(device)
    api.context.undo_stack.push(add_cmd)
    api.dispatch("device_added", device)
    api.dispatch("model_changed", {"action": "add", "item": device})

    # Confirm device is in scene
    items = [item for item in window.canvas.scene.items() if hasattr(item, 'device') and getattr(item, 'device', None) and getattr(item.device, 'id', None) == dev_id]
    print(f"[TEST] DeviceItems in scene after add: {len(items)}")
    assert items, "DeviceItem not found in scene after add."

    # Remove device using DeleteDeviceCommand
    del_cmd = DeleteDeviceCommand(device)
    api.context.undo_stack.push(del_cmd)
    api.dispatch("device_removed", device)
    api.dispatch("model_changed", {"action": "remove", "item": device})
    # Allow event loop to process
    qtbot.wait(100)

    # Confirm device is removed from scene
    items = [item for item in window.canvas.scene.items() if hasattr(item, 'device') and getattr(item, 'device', None) and getattr(item.device, 'id', None) == dev_id]
    print(f"[TEST] DeviceItems in scene after remove: {len(items)}")
    assert not items, "DeviceItem still present in scene after device removal."
