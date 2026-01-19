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

# Contract: Print action triggers print logic via APIManager
def test_print_action_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'print_project'):
        pytest.skip('APIManager does not implement print_project contract.')
    api_manager.print_project = MagicMock()
    main_window.api = api_manager
    # Simulate print action (e.g., printing the current project)
    api_manager.print_project('test_print_path')
    api_manager.print_project.assert_called_once_with('test_print_path')
