import pytest
from PySide6.QtCore import QPointF, Qt
from unittest.mock import MagicMock
from tools.move_tool import MoveTool
from ui.canvas import CanvasEvent
from core.device import Device
from api.manager import APIManager

def test_move_command_bundling(qtbot, clean_api_singleton):
    """
    PH5-UI: Verify that a drag operation results in exactly ONE Undo Command.
    """
    # 1. Setup (Uses the clean singleton from fixture)
    api = clean_api_singleton
    
    # Create a device and add it
    import uuid
    dev = Device(id=str(uuid.uuid4()), x=0, y=0)
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev)
    
    # Mock required API attributes for MoveTool hit testing
    api.scene = MagicMock()
    api.view = MagicMock()
    api.view.transform.return_value = MagicMock()
    api.scene.itemAt.return_value = None  # No fallback item

    # 2. ISOLATION: Clear the stack to ignore setup commands
    api.context.undo_stack.clear()
    assert len(api.context.undo_stack) == 0, "Stack failed to clear before test"

    # 3. Initialize Tool
    tool = MoveTool()
    
    # Create a DeviceItem for the device
    from ui.items.device import DeviceItem
    item = DeviceItem(dev)

    # 4. Simulate Drag Interaction (0,0 -> 100,100)
    # PRESS
    press_evt = MagicMock()
    press_evt.scene_pos = QPointF(0, 0)
    press_evt.button.return_value = Qt.LeftButton
    tool.start_drag(item, QPointF(0, 0))
    
    # MOVE
    move_evt = MagicMock()
    move_evt.scene_pos = QPointF(50, 50)
    move_evt.buttons.return_value = Qt.LeftButton
    tool.update_drag(QPointF(50, 50))
    
    # RELEASE
    release_evt = MagicMock()
    release_evt.scene_pos = QPointF(100, 100)
    release_evt.button.return_value = Qt.LeftButton
    tool.finish_drag(QPointF(100, 100))
    
    # 5. Verification
    # Debug print using _undo_stack (safe internal list)
    stack_content = [type(c).__name__ for c in getattr(api.context.undo_stack, '_undo_stack', [])]
    
    assert len(api.context.undo_stack) == 1, \
        f"Bundling Failed: Expected 1 command, found {len(api.context.undo_stack)}. Stack: {stack_content}"

    # Verify the command is actually a Move logic
    # Use _undo_stack directly or peek() if available
    cmd = api.context.undo_stack._undo_stack[0]
    from api.commands.move import MoveCommand
    assert isinstance(cmd, MoveCommand), f"Undo stack did not contain MoveCommand, got {type(cmd)}"
    assert cmd.new_pos == (100.0, 100.0)