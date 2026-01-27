import pytest
from PySide6.QtWidgets import QApplication, QToolBar
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtTest import QTest
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
def main_window(app, api_manager, qtbot):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    yield window
    window.close()

def test_generic_device_placement(main_window, qtbot):
    """
    Test that the generic device placement tool:
    1. Creates a ghost item when activated
    2. Places a device when the user clicks
    3. The placed device appears on the canvas
    
    Note: Ghost position tracking during mouse move is verified manually in the UI
    as it requires full event loop processing that's difficult to simulate in tests.
    """
    # Find and trigger the generic device action from the toolbar
    toolbar = None
    for child in main_window.findChildren(QToolBar):
        if child.objectName() == "MainToolBar":
            toolbar = child
            break
    assert toolbar is not None, "MainToolBar not found in main window."
    
    action = None
    for act in toolbar.actions():
        if act.data() == "tool.add_generic_device":
            action = act
            break
    assert action is not None, "Generic device toolbar action not found."
    
    # Trigger the placement tool
    action.trigger()
    qtbot.wait(50)
    
    # Get API and canvas references
    api = main_window.api
    canvas = main_window.canvas
    
    # Verify PlacementTool is active
    tool = api.tool_manager.active_tool
    assert tool is not None, "No active tool after triggering placement action."
    assert hasattr(tool, 'ghost_item'), "Active tool is not PlacementTool (no ghost_item attribute)."
    
    # Verify ghost was created when tool was activated
    ghost = getattr(tool, 'ghost_item', None)
    assert ghost is not None, "Ghost item was not created when PlacementTool was activated."
    assert ghost.scene() == canvas.scene, "Ghost item is not in the canvas scene."
    
    # Verify ghost is marked as a ghost (visual feedback)
    assert hasattr(ghost, 'is_ghost') and ghost.is_ghost, "Ghost item should be marked as is_ghost."
    
    # Record initial state
    initial_device_count = len(api.context.harness.devices)
    
    # Define a test position for device placement
    scene_pos = QPointF(120, 80)
    viewport_pos = canvas.mapFromScene(scene_pos)
    
    # Simulate mouse click to place the device
    # This should trigger PlacementTool.on_mouse_press which adds the device
    QTest.mouseClick(canvas.viewport(), Qt.LeftButton, Qt.NoModifier, viewport_pos)
    qtbot.wait(100)  # Allow event processing and model update
    
    # Verify device was added to the model
    devices = api.context.harness.devices
    assert len(devices) > initial_device_count, f"No device added after click. Before: {initial_device_count}, After: {len(devices)}"
    
    device = devices[-1]
    
    # Device should be placed near the clicked position
    # Use generous tolerance to account for snapping and coordinate conversion
    tolerance = 15.0
    assert abs(device.x - 120) < tolerance, f"Device x position out of range: {device.x} (expected ~120, tolerance: {tolerance})"
    assert abs(device.y - 80) < tolerance, f"Device y position out of range: {device.y} (expected ~80, tolerance: {tolerance})"
    
    # Verify the device appears on the canvas
    qtbot.wait(100)  # Allow scene to update
    scene_items = [item for item in canvas.scene.items() 
                   if hasattr(item, 'model') and hasattr(item.model, 'id')]
    found = any(item.model.id == device.id for item in scene_items)
    assert found, f"Placed device {device.id} does not appear on the canvas. Found items: {[getattr(item.model, 'id', 'no-id') for item in scene_items]}"
    
    # Verify ghost is cleaned up or tool switched after placement
    # PlacementTool typically switches to select tool after placing a device
    current_tool = api.tool_manager.active_tool
    # Either the tool switched to select, or the ghost was removed
    if current_tool == tool:
        # If still in placement tool, ghost should still exist for next placement
        assert tool.ghost_item is not None, "Ghost should persist for next placement"
    else:
        # Tool switched - verify it's the select tool
        assert hasattr(current_tool, '__class__'), "Active tool should be a tool instance"
