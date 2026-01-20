import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF, Qt
from tools.move_tool import MoveTool
from ui.canvas import CanvasEvent
from core.device import Device
from api.commands.move import MoveCommand

def test_move_tool_pushes_command(clean_api_singleton):
    """
    Verifies that the MoveTool pushes exactly ONE command to the UndoStack
    upon mouse release, matching the new 'Command Bundling' architecture.
    """
    api = clean_api_singleton
    api.context.undo_stack.clear()
    
    # 1. Setup
    device = Device(id="d1", x=0.0, y=0.0)
    api.context.harness.devices.append(device)
    tool = MoveTool()
    
    # 2. Simulate Drag (0,0 -> 50,50)
    
    # Press
    evt_press = MagicMock()
    evt_press.scene_pos = QPointF(0, 0)
    evt_press.button.return_value = Qt.LeftButton
    # Create a mock item wrapper like the actual UI uses
    mock_item = MagicMock()
    mock_item.model = device
    mock_item.parentItem.return_value = None
    mock_item.pos.return_value = QPointF(0, 0)
    
    tool.on_mouse_press(CanvasEvent(evt_press, QPointF(0, 0), scene_item=mock_item, item_at=mock_item))
    
    # Move
    evt_move = MagicMock()
    evt_move.scene_pos = QPointF(50, 50)
    evt_move.buttons.return_value = Qt.LeftButton
    tool.on_mouse_move(CanvasEvent(evt_move, QPointF(50, 50), scene_item=mock_item, item_at=mock_item))
    
    # ASSERTION: No command should be pushed YET
    assert len(api.context.undo_stack) == 0, "MoveTool pushed a command during the drag (should be bundled)."
    
    # Release
    evt_release = MagicMock()
    evt_release.scene_pos = QPointF(50, 50)
    evt_release.button.return_value = Qt.LeftButton
    tool.on_mouse_release(CanvasEvent(evt_release, QPointF(50, 50), scene_item=mock_item, item_at=mock_item))
    
    # 3. Final Verification
    assert len(api.context.undo_stack) == 1, "MoveTool failed to push command on release."
    cmd = api.context.undo_stack._undo_stack[0]
    assert isinstance(cmd, MoveCommand)
    assert cmd.new_pos == (50.0, 50.0)