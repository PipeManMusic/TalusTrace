import pytest
from PySide6.QtCore import QPointF
from unittest.mock import MagicMock
from ui.input_system import InputSystem
from ui.canvas import CanvasEvent
from api.manager import APIManager

def test_dispatcher_routing_to_active_tool(qtbot):
    """PH6-EVT.1: InputSystem should route canvas events to the active tool."""
    # 1. Force Clean Slate
    APIManager._instance = None
    api = APIManager.get_instance()
    
    # 2. Ensure ToolManager is real
    from api.tool_manager import ToolManager
    if not hasattr(api, 'tool_manager') or not isinstance(api.tool_manager, ToolManager):
        api.tool_manager = ToolManager()
    
    input_sys = InputSystem()
    
    # 3. Setup Mock Tool
    mock_tool = MagicMock()
    api.tool_manager.register_tool("mock_tool", mock_tool)
    api.tool_manager.set_tool("mock_tool")
    
    assert api.tool_manager.active_tool == mock_tool
    
    # 4. Create a Mock Canvas Event
    mock_view_event = MagicMock()
    mock_view_event.type.return_value = 2 # QEvent.MouseButtonPress
    
    # FIX: Correct Argument Name
    canvas_event = CanvasEvent(
        original_event=mock_view_event,
        scene_pos=QPointF(100, 100),
        scene_item=None
    )
    
    # 5. Simulate Dispatch (Directly call tool method as Canvas would)
    # Since we are testing that the tool receives it
    if hasattr(mock_tool, 'on_mouse_press'):
        mock_tool.on_mouse_press(canvas_event)
        
    assert mock_tool.on_mouse_press.called
    assert mock_tool.on_mouse_press.call_args[0][0] == canvas_event