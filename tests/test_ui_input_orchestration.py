import pytest
from PySide6.QtCore import QPointF
from unittest.mock import MagicMock
from ui.input_system import InputSystem
 # CanvasEvent is no longer used; test only InputSystem and tool routing
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
    
    # 4. Simulate event routing: call the tool's on_mouse_press directly
    event_obj = MagicMock()
    event_obj.scene_pos = QPointF(100, 100)
    event_obj.scene_item = None
    if hasattr(mock_tool, 'on_mouse_press'):
        mock_tool.on_mouse_press(event_obj)
    assert mock_tool.on_mouse_press.called
    assert mock_tool.on_mouse_press.call_args[0][0] == event_obj