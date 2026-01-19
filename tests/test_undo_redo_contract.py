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

# Contract: Undo/redo actions via the action system update application state
def test_undo_redo_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.context = MagicMock()
    api_manager.context.undo_stack = MagicMock()
    api_manager.context.undo_stack.undo = MagicMock()
    api_manager.context.undo_stack.redo = MagicMock()
    main_window.api = api_manager
    main_window.register_toolbar_commands()
    from api.actions import dispatch_action
    # Simulate undo action
    dispatch_action('edit.undo')
    api_manager.context.undo_stack.undo.assert_called_once()
    # Simulate redo action
    dispatch_action('edit.redo')
    api_manager.context.undo_stack.redo.assert_called_once()
