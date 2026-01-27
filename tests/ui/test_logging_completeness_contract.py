import os
# Set env vars before any other imports
os.environ["TALUSTRACE_INFRA_LOG"] = "1"
os.environ["TALUSTRACE_LOG_PATH"] = "/tmp/talustrace_test_debug.log"
print(f"[test setup] TALUSTRACE_INFRA_LOG={os.environ.get('TALUSTRACE_INFRA_LOG')}")
print(f"[test setup] TALUSTRACE_LOG_PATH={os.environ.get('TALUSTRACE_LOG_PATH')}")

import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from api.actions import register_device_command_actions
register_device_command_actions()
from core.device import Device, Pin
from core.harness import DeviceList
from infra.context import Context
import uuid
from PySide6.QtCore import Qt

def test_pin_context_menu_delete_logs(qtbot, tmp_path):
    """
    Contract: Deleting a pin via context menu must produce infra_log entries for start/complete of DeletePinCommand.execute.
    """

    # Setup log file path (override for this test instance)
    log_path = tmp_path / "talustrace_test.log"
    os.environ["TALUSTRACE_LOG_PATH"] = str(log_path)
    os.environ["TALUSTRACE_INFRA_LOG"] = "1"
    print(f"[test body] TALUSTRACE_INFRA_LOG={os.environ.get('TALUSTRACE_INFRA_LOG')}")
    print(f"[test body] TALUSTRACE_LOG_PATH={os.environ.get('TALUSTRACE_LOG_PATH')}")

    app = QApplication.instance() or QApplication([])
    APIManager.reset()
    api = APIManager(context=Context())
    window = MainWindow()
    window.api = api
    api.main_window = window
    window.show()
    qtbot.addWidget(window)

    # Add a device and pin
    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=100, y=100, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    pin = Pin(id=pin_id, x=10, y=10, label="TestPin", side=0, device_id=device_id)
    device.pins.append(pin)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    api.dispatch("model_changed", {"action": "add", "item": device})
    api.dispatch("model_changed", {"action": "add", "item": pin})

    # Load harness and get PinItem
    window.canvas.load_harness(api.context.harness)
    qtbot.waitUntil(lambda: any(
        hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id
        for item in window.canvas.scene.items()
    ), timeout=2000)

    # Simulate right-click (context menu) event at pin position
    canvas = window.canvas
    # Retrieve PinItem from scene
    pin_item = None
    for item in canvas.scene.items():
        if hasattr(item, 'model') and getattr(item.model, 'id', None) == pin_id:
            pin_item = item
            break
    assert pin_item is not None, "PinItem not found in scene."
    scene_pos = pin_item.scenePos()
    viewport_pos = canvas.mapFromScene(scene_pos)
    pin_item.setSelected(True)
    # Explicitly set selection in both SelectionManager and api.context.selection_manager for dispatcher
    from core.selection import SelectionManager
    sel_mgr = SelectionManager()
    sel_mgr.select(pin)
    api.context.selection_manager = sel_mgr
    qtbot.wait(100)
    qtbot.mouseClick(canvas.viewport(), Qt.RightButton, pos=viewport_pos)
    qtbot.wait(200)
    # Find and trigger the delete action from the menu
    menu = window.context_menu_manager.build_menu(menu_type='pin')
    delete_uuid = 'e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b'
    delete_action = next((a for a in menu.actions()
                         if (a.data() == delete_uuid or (isinstance(a.data(), dict) and a.data().get('uuid') == delete_uuid))
                         or 'delete' in a.text().lower()), None)
    assert delete_action is not None, "Delete action not found in pin context menu."
    delete_action.trigger()
    qtbot.wait(200)

    # Check log file for expected entries
    assert log_path.exists(), "Log file was not created."
    log_content = log_path.read_text()
    assert f"DeletePinCommand.execute START for pin UUID={pin_id}" in log_content, "DeletePinCommand execute start log missing."
    assert f"DeletePinCommand.execute COMPLETE for pin UUID={pin_id}" in log_content, "DeletePinCommand execute complete log missing."
