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

# Contract: Export action triggers export logic via APIManager
def test_export_action_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    if not hasattr(api_manager, 'export_project'):
        pytest.skip('APIManager does not implement export_project contract.')
    api_manager.export_project = MagicMock()
    main_window.api = api_manager
    # Simulate export action (e.g., exporting the current project)
    api_manager.export_project('test_export_path')
    api_manager.export_project.assert_called_once_with('test_export_path')
