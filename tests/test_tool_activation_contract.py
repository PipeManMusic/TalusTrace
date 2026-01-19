import pytest
from unittest.mock import MagicMock
from ui.main_window import MainWindow
from api.manager import APIManager

@pytest.fixture
def main_window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Tool activation via action system sets the correct active tool
def test_tool_activation_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.tool_manager = MagicMock()
    api_manager.tool_manager.set_tool = MagicMock()
    main_window.api = api_manager
    # Register toolbar commands (includes tool.add_generic_device)
    main_window.register_toolbar_commands()
    from api.actions import dispatch_action
    dispatch_action('tool.add_generic_device')
    api_manager.tool_manager.set_tool.assert_called_once_with('placement')
