import os
import pytest
from PySide6.QtCore import Qt, QPointF
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import MagicMock


def test_right_click_on_device_shows_context_menu(qtbot):
    """
    Contract: Right-clicking on a device should show the context menu, not deselect the device.
    """
    # Setup main window and API
    window = MainWindow()
    qtbot.addWidget(window)
    is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
    if not is_headless:
        window.show()
    api = window.api
    # Patch APIManager.open_context_menu to track calls
    api.open_context_menu = MagicMock(wraps=api.open_context_menu)
    # Add a device to the model and scene
    from core.models import Device
    device = Device(id="test_device", x=100.0, y=100.0, meta={"width_mm": 40.0, "height_mm": 30.0})
    api.context.harness.devices.append(device)
    window.canvas.load_harness(api.context.harness)
    item = api.get_scene_item(device.id)
    assert item is not None, "DeviceItem not found in scene registry."
    # Simulate right-click (context menu) event at device position
    scene = item.scene()
    view = scene.views()[0]
    device_center = item.scenePos() + item.boundingRect().center()
    viewport_pos = view.mapFromScene(device_center)
    # Select the device first
    item.setSelected(True)
    # Right-click on the device
    qtbot.mouseClick(view.viewport(), Qt.RightButton, pos=viewport_pos)
    # Assert device is still selected
    assert item.isSelected(), "Device was deselected on right-click."
    # Assert context menu was shown
    assert api.open_context_menu.call_count > 0, "Context menu was not shown on device right-click."
