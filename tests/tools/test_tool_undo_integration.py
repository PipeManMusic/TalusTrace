import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF, Qt
from tools.move_tool import MoveTool
 # CanvasEvent is no longer used; test only MoveTool and model/undo stack behavior
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
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0.0, y=0.0)
    from core.harness import DeviceList
    with DeviceList.test_bypass():
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
    
    tool.start_drag(mock_item, QPointF(0, 0))
    
    # Move
    evt_move = MagicMock()
    evt_move.scene_pos = QPointF(50, 50)
    evt_move.buttons.return_value = Qt.LeftButton
    tool.update_drag(QPointF(50, 50))
    
    # ASSERTION: No command should be pushed YET
    assert len(api.context.undo_stack) == 0, "MoveTool pushed a command during the drag (should be bundled)."
    
    # Release
    evt_release = MagicMock()
    evt_release.scene_pos = QPointF(50, 50)
    evt_release.button.return_value = Qt.LeftButton
    tool.finish_drag(QPointF(50, 50))
    
    # 3. Final Verification
    assert len(api.context.undo_stack) == 1, "MoveTool failed to push command on release."
    cmd = api.context.undo_stack._undo_stack[0]
    from api.commands.move import MoveCommand
    assert isinstance(cmd, MoveCommand), f"Undo stack did not contain MoveCommand, got {type(cmd)}"
    assert cmd.new_pos == (50.0, 50.0)