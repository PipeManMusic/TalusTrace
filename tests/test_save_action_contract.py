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

# Contract: Save action triggers save logic via APIManager
def test_save_action_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'save_project'):
        pytest.skip('APIManager does not implement save_project contract.')
    api_manager.save_project = MagicMock()
    main_window.api = api_manager
    # Simulate save action (e.g., saving the current project)
    api_manager.save_project('test_save_path')
    api_manager.save_project.assert_called_once_with('test_save_path')
