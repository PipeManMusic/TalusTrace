import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt, QPointF
from ui.input_system import InputSystem
from api.manager import APIManager
from ui.canvas import CanvasEvent

def test_dispatcher_routing_to_active_tool(qtbot):
    """PH6-EVT.1: InputSystem should route canvas events to the active tool."""
    input_sys = InputSystem()
    api = APIManager.get_instance()
    
    # 1. Setup Mock Tool
    mock_tool = MagicMock()
    api.tool_manager.register_tool("mock_tool", mock_tool)
    api.tool_manager.set_tool("mock_tool")
    
    # 2. Create a Mock Canvas Event
    mock_event = MagicMock()
    # Simulate a MousePress event type
    mock_event.type.return_value = 2 # QEvent.MouseButtonPress
    
    canvas_event = CanvasEvent(
        view_event=mock_event,
        scene_pos=QPointF(100, 100),
        scene=MagicMock(),
        scene_item=None
    )
    
    # 3. Dispatch via InputSystem
    input_sys.handle_canvas_event(canvas_event)
    
    # 4. Verify the correct tool method was called
    mock_tool.on_mouse_press.assert_called_once_with(canvas_event)

def test_dispatcher_graceful_no_tool(qtbot):
    """PH6-EVT.1: InputSystem should not crash if no tool is active."""
    input_sys = InputSystem()
    api = APIManager.get_instance()
    api.tool_manager.set_tool(None) # Clear tool
    
    mock_event = MagicMock()
    mock_event.type.return_value = 2
    canvas_event = CanvasEvent(mock_event, QPointF(0,0), None)
    
    # Should complete without exception
    input_sys.handle_canvas_event(canvas_event)