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
    # Simulate a mouse press event to place the device
    canvas = main_window.canvas
    api = main_window.api
    # Place at (100, 100)
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import Qt, QPoint
    event = QMouseEvent(QMouseEvent.MouseButtonPress, QPoint(100, 100), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    canvas.mousePressEvent(event)
    # Check that a device was added to the model
    devices = api.context.harness.devices
    assert devices, "No devices added to the model after placement."
    device = devices[-1]
    assert isinstance(device, Device), "Placed item is not a Device."
    # Check for errors in device properties
    scene_pt = canvas.mapToScene(100, 100)
    assert abs(device.x - scene_pt.x()) < 3.0, f"Device x position incorrect: {device.x} != {scene_pt.x()}"
    assert abs(device.y - scene_pt.y()) < 3.0, f"Device y position incorrect: {device.y} != {scene_pt.y()}"
    assert device.meta.get('_type', 'generic') == 'generic', f"Device type incorrect: {device.meta.get('_type')}"
    # Check that the device appears on the canvas
    scene_items = [item for item in canvas.scene.items() if hasattr(item, 'device')]
    found = any(getattr(item.device, 'id', None) == device.id for item in scene_items)
    assert found, "Placed device does not appear on the canvas."
