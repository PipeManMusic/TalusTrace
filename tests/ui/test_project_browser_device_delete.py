import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from PySide6.QtCore import Qt

def test_project_browser_updates_on_device_delete(qtbot):
    """
    Ensure the project browser updates and removes a device from its list when the device is deleted.
    """
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = window.api
    # Add a device to the model and scene
    from core.models import Device
    import uuid
    device = Device(id=str(uuid.uuid4()), x=100.0, y=100.0, meta={"width_mm": 40.0, "height_mm": 30.0})
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    window.canvas.load_harness(api.context.harness)
    # Find the project browser widget (assume it's accessible as window.project_browser or similar)
    project_browser = getattr(window, 'project_browser', None)
    assert project_browser is not None, "Project browser not found on MainWindow."
    # Confirm device is listed
    device_ids = [d.id for d in getattr(project_browser, 'devices', [])]
    assert device.id in device_ids, "Device not listed in project browser before deletion."
    # Delete the device using the command pattern
    from api.commands.device import DeleteDeviceCommand
    cmd = DeleteDeviceCommand(device)
    cmd.execute()
    qtbot.wait(100)  # Allow signal processing
    # Confirm device is no longer listed
    device_ids_after = [d.id for d in getattr(project_browser, 'devices', [])]
    assert device.id not in device_ids_after, "Device still listed in project browser after deletion."
