import pytest
from api.manager import APIManager
from ui.dialogs.device_wizard import DeviceWizard
from PySide6.QtCore import Qt
from ui.main_window import MainWindow

@pytest.mark.usefixtures("qtbot")
def test_device_wizard_duplicate_device_items_catch(qtbot):
    """
    Simulate the full UI flow: use DeviceWizard to create a device and ensure only one DeviceItem is created in the scene.
    This test is designed to fail if two DeviceItems are created for a single user action.
    """
    APIManager.reset()
    api = APIManager.get_instance()
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    wizard = DeviceWizard()
    wizard.name_input.setText("Test Device")
    ok_button = wizard.accept_button
    if ok_button.isEnabled():
        qtbot.mouseClick(ok_button, Qt.LeftButton)
    else:
        wizard.accept()
    # After creation, check DeviceItems in the canvas scene
    canvas = win.canvas
    from ui.items.device import DeviceItem
    device_items = [item for item in canvas.scene.items() if isinstance(item, DeviceItem)]
    device_ids = [item.model.id for item in device_items]
    from collections import Counter
    id_counts = Counter(device_ids)
    duplicates = [dev_id for dev_id, count in id_counts.items() if count > 1]
    assert not duplicates, f"Duplicate DeviceItems found for device_ids: {duplicates}"
    harness_ids = [dev.id for dev in api.context.harness.devices]
    assert len(device_items) == len(harness_ids), f"Expected {len(harness_ids)} DeviceItems, found {len(device_items)}"
