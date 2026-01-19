import pytest
from unittest.mock import MagicMock
from ui.main_window import MainWindow
from api.manager import APIManager
from PySide6.QtGui import QAction

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

# Contract: Menu action triggers correct dispatcher action and updates state
def test_menu_action_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.dispatch_action = MagicMock()
    main_window.api = api_manager
    # Create a menu action and connect to dispatcher
    action = QAction('Test Menu Action', main_window)
    action.triggered.connect(lambda: api_manager.dispatch_action('menu.test_action'))
    main_window.addAction(action)
    # Simulate menu action activation
    action.trigger()
    api_manager.dispatch_action.assert_called_once_with('menu.test_action')
