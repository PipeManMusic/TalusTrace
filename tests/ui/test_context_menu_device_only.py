import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from PySide6.QtCore import Qt, QPoint

def test_context_menu_only_on_device(qtbot):
    """
    Ensure the device context menu is only shown when right-clicking directly on a device.
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
    item = api.get_scene_item(device.id)
    assert item is not None, "DeviceItem not found in scene registry."
    # Install a test hook for context menu
    shown_menu_types = []
    def test_hook(data):
        shown_menu_types.append(data.get('menu_type'))
    api.subscribe('context_menu', test_hook)
    # Right-click on the device (should show device menu)
    scene_pos = item.scenePos()
    viewport_pos = window.canvas.mapFromScene(scene_pos)
    qtbot.mouseClick(window.canvas.viewport(), Qt.RightButton, pos=viewport_pos)
    # Right-click on empty canvas (should show canvas menu)
    empty_pos = QPoint(10, 10)  # Assume this is not over any device
    qtbot.mouseClick(window.canvas.viewport(), Qt.RightButton, pos=empty_pos)
    # Assert the first menu was 'device', the second was 'canvas'
    assert shown_menu_types[0] == 'device', f"Expected 'device' menu, got {shown_menu_types[0]}"
    assert shown_menu_types[1] == 'canvas', f"Expected 'canvas' menu, got {shown_menu_types[1]}"
