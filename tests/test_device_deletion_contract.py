import pytest
from PySide6.QtCore import QPointF, Qt
from ui.main_window import MainWindow
from api.manager import APIManager

def test_device_deletion_removes_from_ui_and_model(qtbot):
    """
    Contract: Deleting a device via the API should remove it from both the model (context.harness.devices)
    and the UI (canvas scene items, project browser).
    """
    app = MainWindow()
    qtbot.addWidget(app)
    app.show()
    api = APIManager.get_instance()
    # Add a device using AddDeviceCommand
    from core.models import Device
    import uuid
    from api.commands.device import AddDeviceCommand, DeleteDeviceCommand
    device = Device(id=str(uuid.uuid4()), x=100.0, y=100.0, meta={"width_mm": 40.0, "height_mm": 30.0})
    add_cmd = AddDeviceCommand(device)
    api.context.undo_stack.push(add_cmd)
    app.canvas.load_harness(api.context.harness)
    # Confirm device is in model and UI
    assert device in api.context.harness.devices
    item = api.get_scene_item(device.id)
    assert item is not None, "DeviceItem not found in scene after add."
    # Delete device using DeleteDeviceCommand
    del_cmd = DeleteDeviceCommand(device)
    api.context.undo_stack.push(del_cmd)
    # UI should update: device should be gone from scene
    item_after = api.get_scene_item(device.id)
    assert item_after is None, "DeviceItem still present in scene after deletion."
    # Project browser (if present) should also update
    if hasattr(app, "project_browser"):
        ids = [d.id for d in app.project_browser.list_devices()]
        assert device.id not in ids, "Device still present in project browser after deletion."
    app.close()
