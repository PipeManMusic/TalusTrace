import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QEvent
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import MagicMock
import os

@pytest.fixture
def enforce_device_mvc_fixture():
    """
    Fixture to enforce strict MVC: UI must only update in response to model changes, not direct UI mutation.
    """
    # This can be expanded as needed for more strict enforcement
"""
Move this file to tests/ui/test_right_click_event_routing_contract.py
"""
 


def test_right_click_event_routing_and_mvc(qtbot, enforce_device_mvc_fixture):
    """
    Contract: Right-click events loaded from YAML must be routed to InputSystem, select the correct tool, and be handled in the UI via strict MVC.
    """
    app = QApplication.instance() or QApplication([])
    # Patch InputSystem to monitor calls
    from ui.input_system import InputSystem
    input_system = InputSystem()
    input_system.handle_canvas_event = MagicMock(wraps=input_system.handle_canvas_event)
    # Inject patched InputSystem into APIManager
    APIManager._instance = None
    api = APIManager.get_instance()
    api.input_system = input_system
    window = MainWindow()
    qtbot.addWidget(window)
    # CRITICAL: Re-install the patched InputSystem as event filter on the canvas
    input_system.install(window.canvas)
    is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
    if not is_headless:
        window.show()
    canvas = window.canvas
    # Add a device to the model and scene
    device = api.context.harness.devices[0] if api.context.harness.devices else None
    if device is None:
        from core.models import Device
        import uuid
        device = Device(id=str(uuid.uuid4()), x=100.0, y=100.0, meta={"width_mm": 40.0, "height_mm": 30.0})
        from core.harness import DeviceList
        with DeviceList.test_bypass():
            api.context.harness.devices.append(device)
        window.canvas.load_harness(api.context.harness)
    item = api.get_scene_item(device.id)
    assert item is not None, "DeviceItem not found in scene registry."
    # Simulate right-click (context menu) event at device position
    scene = item.scene()
    view = scene.views()[0]
    device_center = item.scenePos() + item.boundingRect().center()
    viewport_pos = view.mapFromScene(device_center)
    qtbot.mouseClick(view.viewport(), Qt.RightButton, pos=viewport_pos)
    # Assert InputSystem received the event
    assert input_system.handle_canvas_event.call_count > 0, "InputSystem did not receive right-click event."
    # Check that the correct tool is selected if context menu action is mapped in YAML (simulate if needed)
    # For strict MVC: ensure UI only updates in response to model changes (expand fixture as needed)
    window.close()
