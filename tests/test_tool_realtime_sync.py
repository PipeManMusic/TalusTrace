
import pytest
from api.manager import APIManager
from core.device import Device
from ui.items.device import DeviceItem
from tools.move_tool import MoveTool
from infra.undo_stack import UndoStack

def test_move_tool_realtime_model_sync(qtbot):
    """PH6-EVT.3: Device model coordinates must update during dragging."""
    api = APIManager.get_instance()
    # Force clean state
    api.context.undo_stack = UndoStack()

    dev = Device(id="SYNC_DEV", x=0, y=0)
    item = DeviceItem(dev)

    tool = MoveTool()
    # Ensure tool manager is ready (mock or real, but we assume real API structure)
    if not hasattr(api, 'tool_manager') or isinstance(api.tool_manager, tuple):
        from api.tool_manager import ToolManager
        api.tool_manager = ToolManager()
    api.tool_manager.register_tool("move", tool)
    api.tool_manager.set_tool("move")

    from unittest.mock import MagicMock
    from ui.canvas import CanvasEvent
    from PySide6.QtCore import QPointF, Qt

    # Always use a MagicMock for the view event, with .button() returning Qt.LeftButton
    mock_view_event = MagicMock()
    mock_view_event.button.return_value = Qt.LeftButton
    mock_view_event.pos.return_value = QPointF(0,0)

    # Start Drag
    press_event = CanvasEvent(mock_view_event, QPointF(0,0), None, item)
    tool.on_mouse_press(press_event)

    # Drag to new position
    move_event = CanvasEvent(mock_view_event, QPointF(50, 50), None, item)
    tool.on_mouse_move(move_event)

    # Verify Model is updated BEFORE release
    assert dev.x == 50.0

def test_move_command_bundling(qtbot):
    """PH6-EVT.4: Multiple move events should result in one Undo command."""
    api = APIManager.get_instance()
    # CRITICAL FIX: Restore real UndoStack to allow len() checks
    api.context.undo_stack = UndoStack()

    dev = Device(id="BUNDLE_DEV", x=0, y=0)
    item = DeviceItem(dev)
    tool = MoveTool()

    # Sequence: Press -> Move -> Move -> Release
    from ui.canvas import CanvasEvent
    from PySide6.QtCore import QPointF, QEvent, Qt
    from unittest.mock import MagicMock

    # Create a proper Mock View Event
    mock_view = MagicMock()
    mock_view.type.return_value = QEvent.MouseButtonPress
    mock_view.button.return_value = Qt.LeftButton
    mock_view.pos.return_value = QPointF(0,0)

    # Pass to CanvasEvent
    tool.on_mouse_press(CanvasEvent(mock_view, QPointF(0,0), None, item))
    tool.on_mouse_move(CanvasEvent(mock_view, QPointF(10,10), None, item))
    tool.on_mouse_move(CanvasEvent(mock_view, QPointF(20,20), None, item))
    tool.on_mouse_release(CanvasEvent(mock_view, QPointF(20,20), None, item))

    # Should have 1 command in stack
    assert len(api.context.undo_stack) == 1