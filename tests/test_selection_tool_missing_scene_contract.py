import pytest
from unittest.mock import MagicMock
from api.manager import APIManager
from ui.input_system import InputSystem
from PySide6.QtCore import Qt

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Selection tool should raise AttributeError if APIManager.scene is missing
def test_selection_tool_missing_scene_contract(api_manager):
    api_manager.input_system = InputSystem()
    # Simulate a tool with missing scene attribute
    class DummyEvent:
        scene_pos = MagicMock()
        button = Qt.LeftButton
    from tools.select_tool import SelectTool
    select_tool = SelectTool()
    select_tool.api = api_manager
    api_manager.tool_manager = MagicMock()
    api_manager.tool_manager.active_tool = select_tool
    # Remove scene attribute if present
    if hasattr(api_manager, 'scene'):
        delattr(api_manager, 'scene')
    # Expect AttributeError when handling canvas event
    with pytest.raises(AttributeError):
        select_tool.on_mouse_press(DummyEvent())
