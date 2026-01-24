import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF, Qt
from tools.move_tool import MoveTool
from ui.canvas import CanvasEvent
from core.device import Device
from api.manager import APIManager

def make_mock_graphics_item_for_device(device):
    mock_item = MagicMock()
    mock_item.model = device
    mock_item.parentItem.return_value = None
    mock_item.setPos = MagicMock()
    mock_item.pos.return_value = QPointF(device.x, device.y)
    return mock_item

def test_move_tool_calculates_delta_and_calls_api(clean_api_singleton):
    """
    Verifies that the MoveTool:
    1. Updates the device model DIRECTLY during the drag (Real-time sync).
    2. Pushes a MoveCommand to the UndoStack on release.
    """
    # 1. Setup
    api = clean_api_singleton
    api.context.undo_stack.clear()
    
    # Create a dummy device
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0.0, y=0.0)
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    
    # Initialize Tool
    tool = MoveTool()
    
    # Create a mock QGraphicsItem wrapper for the device
    mock_item = make_mock_graphics_item_for_device(device)
    
    # 2. Simulate Drag: (0,0) -> (10, 10)
    
    # PRESS
    evt_press = MagicMock()
    evt_press.scene_pos = QPointF(0, 0)
    evt_press.button.return_value = Qt.LeftButton
    tool.start_drag(mock_item, QPointF(0, 0))
    
    # Verify dragging started
    assert tool.is_dragging is True, "MoveTool failed to enter drag state on press."
    
    # MOVE
    evt_move = MagicMock()
    evt_move.scene_pos = QPointF(10, 10)
    evt_move.buttons.return_value = Qt.LeftButton
    tool.update_drag(QPointF(10, 10))
    
    # 3. Assert Real-Time Model Update (The bundling logic)
    # The tool should have called APIManager.move_device, which updates device.x/y
    assert device.x == 10.0, f"Real-time update failed. Expected x=10.0, got {device.x}"
    assert device.y == 10.0, f"Real-time update failed. Expected y=10.0, got {device.y}"
    
    # RELEASE
    evt_release = MagicMock()
    evt_release.scene_pos = QPointF(10, 10)
    evt_release.button.return_value = Qt.LeftButton
    tool.finish_drag(QPointF(10, 10))
    
    # 4. Assert Command Push
    assert len(api.context.undo_stack) == 1, "MoveTool failed to push command on release."
    
    cmd = api.context.undo_stack._undo_stack[0]
    from api.commands.move import MoveCommand
    assert isinstance(cmd, MoveCommand), f"Undo stack did not contain MoveCommand, got {type(cmd)}"
    assert cmd.new_pos == (10.0, 10.0), f"Command stored wrong position: {cmd.new_pos}"