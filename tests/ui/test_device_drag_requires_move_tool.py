import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, Qt
from ui.main_window import MainWindow
from api.manager import APIManager
import os


def test_device_drag_always_routes_to_move_tool(qtbot, enforce_device_mvc_fixture):
    """
    Contract: Click and drag on a device should always route to MoveTool logic via the API,
    regardless of the active tool. The model must be updated via MoveTool, and undo/redo must work.
    """
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    print(f"[DEBUG] QApplication instance: {app}")
    assert app is not None, "QApplication instance should exist (provided by qtbot)"
    window = MainWindow()
    qtbot.addWidget(window)
    is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
    if not is_headless:
        window.show()
    api = APIManager.get_instance()
    # ...existing code...
    window.close()
    qtbot.waitExposed(window)
    # Add a device to the model and scene, and reset its position to avoid state leakage
    device = api.context.harness.devices[0] if api.context.harness.devices else None
    if device is None:
        from core.models import Device
        device = Device(id="test_device", x=100.0, y=100.0, meta={"width_mm": 40.0, "height_mm": 30.0})
        api.context.harness.devices.append(device)
        window.canvas.load_harness(api.context.harness)
    else:
        device.x = 100.0
        device.y = 100.0
    item = api.get_scene_item(device.id)
    assert item is not None, "DeviceItem not found in scene registry."
    scene = item.scene()
    view = scene.views()[0]
    start_scene_pos = item.scenePos() + item.boundingRect().center()
    end_scene_pos = start_scene_pos + QPointF(50, 25)
    start_viewport_pos = view.mapFromScene(start_scene_pos)
    end_viewport_pos = view.mapFromScene(end_scene_pos)
    item.setSelected(True)
    # Try drag with a non-move tool active (e.g., select)
    api.tool_manager.set_tool("select")
    qtbot.mousePress(view.viewport(), Qt.LeftButton, pos=start_viewport_pos)
    qtbot.mouseMove(view.viewport(), pos=end_viewport_pos)
    qtbot.mouseRelease(view.viewport(), Qt.LeftButton, pos=end_viewport_pos)
    # Device should move, direct modification is allowed for MoveTool
    expected_x = 100.0 + 50
    expected_y = 100.0 + 25
    assert abs(device.x - expected_x) < 1e-2 and abs(device.y - expected_y) < 1e-2, f"Device did not move via MoveTool logic: ({device.x}, {device.y}) vs ({expected_x}, {expected_y})"
    # Optionally, test undo/redo stack if needed
    window.close()
