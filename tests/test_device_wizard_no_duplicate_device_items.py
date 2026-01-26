import pytest
from api.manager import APIManager
from ui.dialogs.device_wizard import DeviceWizard
from PySide6.QtCore import Qt

@pytest.mark.usefixtures("qtbot")
def test_device_wizard_no_duplicate_device_items(qtbot):
    """
    Simulate the full UI flow: use DeviceWizard to create a device and ensure only one DeviceItem is created in the scene.
    Regression test for duplicate DeviceItems in the canvas after device creation.
    """
    APIManager.reset()
    api = APIManager.get_instance()
    main_window = None
    # Try to get the main window (if available)
    try:
        from PySide6.QtWidgets import QApplication
        main_window = QApplication.activeWindow()
    except Exception:
        pass
    wizard = DeviceWizard()
    wizard.name_input.setText("Test Device")
    ok_button = wizard.accept_button
    if ok_button.isEnabled():
        qtbot.mouseClick(ok_button, Qt.LeftButton)
    else:
        wizard.accept()
    # After creation, check DeviceItems in the canvas scene
    if main_window and hasattr(main_window, "canvas"):
        canvas = main_window.canvas
        device_ids = [dev.id for dev in api.context.harness.devices]
        scene_items = [item for item in canvas.scene.items() if hasattr(item, "model") and getattr(item.model, "id", None) in device_ids]
        # There should be exactly one DeviceItem per device
        assert len(scene_items) == len(device_ids), f"Expected {len(device_ids)} DeviceItems, found {len(scene_items)}"
    else:
        pytest.skip("Main window or canvas not available for DeviceItem check.")
