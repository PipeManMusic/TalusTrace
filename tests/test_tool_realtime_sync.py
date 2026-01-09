from core.device import Device
from ui.items import DeviceItem
from api.manager import APIManager
from tools.move_tool import MoveTool

def test_move_tool_realtime_model_sync(qtbot):
    """PH6-EVT.3: Device model coordinates must update during dragging."""
    api = APIManager.get_instance()
    dev = Device(id="SYNC_DEV", x=0, y=0)
    item = DeviceItem(dev)
    
    tool = MoveTool()
    api.tool_manager.register_tool("move", tool)
    api.tool_manager.set_tool("move")
    
    # Mock Event at start
    from ui.canvas import CanvasEvent
    from PySide6.QtCore import QPointF
    
    # Start Drag
    press_event = CanvasEvent(None, QPointF(0,0), None, item)
    tool.on_mouse_press(press_event)
    
    # Drag to new position
    move_event = CanvasEvent(None, QPointF(50, 50), None, item)
    tool.on_mouse_move(move_event)
    
    # Verify Model is updated BEFORE release
    assert dev.x == 50.0
    assert dev.y == 50.0

def test_move_command_bundling(qtbot):
    """PH6-EVT.4: Multiple move events should result in one Undo command."""
    api = APIManager.get_instance()
    api.context.undo_stack.clear()
    
    dev = Device(id="BUNDLE_DEV", x=0, y=0)
    item = DeviceItem(dev)
    tool = MoveTool()
    
    # Sequence: Press -> Move -> Move -> Release
    from ui.canvas import CanvasEvent
    from PySide6.QtCore import QPointF
    
    tool.on_mouse_press(CanvasEvent(None, QPointF(0,0), None, item))
    tool.on_mouse_move(CanvasEvent(None, QPointF(10,10), None, item))
    tool.on_mouse_move(CanvasEvent(None, QPointF(20,20), None, item))
    tool.on_mouse_release(CanvasEvent(None, QPointF(20,20), None, item))
    
    # Only 1 command should be on the stack
    assert len(api.context.undo_stack) == 1