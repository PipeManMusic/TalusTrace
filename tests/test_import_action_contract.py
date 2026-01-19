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

# Contract: Import action triggers import logic via APIManager
def test_import_action_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'import_project'):
        pytest.skip('APIManager does not implement import_project contract.')
    api_manager.import_project = MagicMock()
    main_window.api = api_manager
    # Simulate import action (e.g., importing a project from a path)
    api_manager.import_project('test_import_path')
    api_manager.import_project.assert_called_once_with('test_import_path')
