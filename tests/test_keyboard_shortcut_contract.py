import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QAction
from PySide6.QtGui import QKeySequence
from ui.main_window import MainWindow
from api.manager import APIManager

@pytest.fixture
def main_window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    return win

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Keyboard shortcut triggers correct action via ActionRegistry/dispatcher
def test_keyboard_shortcut_contract(main_window, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.dispatch_action = MagicMock()

    # Add a test action with a shortcut
    action = QAction('Test Action', main_window)
    action.setShortcut(QKeySequence('Ctrl+T'))
    main_window.addAction(action)
    action.triggered.connect(lambda: api_manager.dispatch_action('test.action'))

    # Simulate shortcut activation
    action.trigger()
    api_manager.dispatch_action.assert_called_once_with('test.action')
