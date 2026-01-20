import pytest
from PySide6.QtCore import QPointF, Qt
from unittest.mock import MagicMock
from tools.move_tool import MoveTool
from ui.canvas import CanvasEvent
from core.device import Device
from api.manager import APIManager

def test_move_tool_undo_bundling(qtbot):
    """
    Compliance Check: UI Spec 4 (State Synchronization).
    
    Risk: Tool updates device.x/y but forgets to push Command on release.
    Result: Undo Stack is empty or desynchronized.
    """
    # 1. Setup
    APIManager.reset()
    api = APIManager.get_instance()
    
    # Create Device
    dev = Device(id="D1", x=0, y=0)
    api.context.harness.devices.append(dev)
    
    # Setup Tool
    tool = MoveTool()
    tool.start(dev)

    # 2. Simulate Drag (0,0 -> 100,100)
    # Start
    press_evt = MagicMock()
    press_evt.scene_pos = QPointF(0, 0)
    press_evt.button.return_value = Qt.LeftButton
    tool.on_mouse_press(CanvasEvent(press_evt, QPointF(0, 0), scene_item=None, item_at=dev))

    # Move (Real-time update)
    move_evt = MagicMock()
    move_evt.scene_pos = QPointF(50, 50) # Halfway
    move_evt.button.return_value = Qt.LeftButton
    tool.on_mouse_move(CanvasEvent(move_evt, QPointF(50, 50), scene_item=None, item_at=dev))

    # Verify Real-time spec (Spec 4.1)
    assert dev.x == 50.0, "MoveTool failed real-time update requirement"

    # Finish
    release_evt = MagicMock()
    release_evt.scene_pos = QPointF(100, 100)
    release_evt.button.return_value = Qt.LeftButton
    tool.on_mouse_release(CanvasEvent(release_evt, QPointF(100, 100), scene_item=None, item_at=dev))

    assert dev.x == 100.0
    
    # 3. Critical Assertion: Undo Stack
    # Stack should have EXACTLY 1 command (not 0, not 50)
    assert len(api.context.undo_stack) == 1, \
        "VIOLATION: Undo Stack empty! MoveTool modified state but pushed no command."
        
    # 4. Verify Undo Integrity
    api.context.undo_stack.undo()
    assert dev.x == 0.0, "Undo failed to revert position to start."
