import pytest
from PySide6.QtWidgets import QApplication, QToolBar
from ui.main_window import MainWindow
from api.manager import APIManager
from infra.context import Context
from core.device import Device

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    yield api

@pytest.fixture(scope="function")
def main_window(app, api_manager):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    window.show()
    yield window
    window.close()

def test_generic_device_placement(main_window):
    toolbar = None
    for child in main_window.findChildren(QToolBar):
        if child.objectName() == "MainToolBar":
            toolbar = child
            break
    assert toolbar is not None, "MainToolBar not found in main window."
    # Find the generic device action
    action = None
    for act in toolbar.actions():
        if act.data() == "tool.add_generic_device":
            action = act
            break
    assert action is not None, "Generic device toolbar action not found."
    # Simulate clicking the toolbar button
    action.trigger()
    # Ensure PlacementTool is active
    api = main_window.api
    tool = api.tool_manager.get_tool("placement")
    api.tool_manager.set_tool("placement")
    # Simulate a mouse move event to move the ghost
    canvas = main_window.canvas
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import Qt, QPoint
    # Map intended scene position to widget (viewport) coordinates
    scene_x, scene_y = 120, 80
    widget_pt = canvas.mapFromScene(scene_x, scene_y)
    from PySide6.QtCore import QPoint
    move_event = QMouseEvent(QMouseEvent.MouseMove, QPoint(widget_pt.x(), widget_pt.y()), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    canvas.mouseMoveEvent(move_event)

    # Assert: ghost_item should exist and be at (120, 80)
    ghost = getattr(tool, 'ghost_item', None)
    assert ghost is not None, "Ghost item was not created after activating PlacementTool."
    ghost_pos = ghost.pos() if hasattr(ghost, 'pos') else None
    assert ghost_pos is not None, "Ghost item has no position."
    # This should now fail if the ghost does not follow the mouse
    assert abs(ghost_pos.x() - 120) < 3.0 and abs(ghost_pos.y() - 80) < 3.0, f"Ghost not at mouse: {ghost_pos}"

    # Assert: no device added yet
    devices = api.context.harness.devices
    assert not devices, "Device was added before mouse click."

    # Simulate a mouse press event to place the device at the new location
    press_event = QMouseEvent(QMouseEvent.MouseButtonPress, QPoint(widget_pt.x(), widget_pt.y()), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    canvas.mousePressEvent(press_event)

    # Assert: device is now added at (120, 80)
    devices = api.context.harness.devices
    assert devices, "No device added after mouse click."
    device = devices[-1]
    assert abs(device.x - 120) < 3.0, f"Device x position incorrect: {device.x} != 120"
    assert abs(device.y - 80) < 3.0, f"Device y position incorrect: {device.y} != 80"
    assert device.meta.get('_type', 'generic') == 'generic', f"Device type incorrect: {device.meta.get('_type')}"
    # Check that the device appears on the canvas
    scene_items = [item for item in canvas.scene.items() if hasattr(item, 'device')]
    found = any(getattr(item.device, 'id', None) == device.id for item in scene_items)
    assert found, "Placed device does not appear on the canvas."
