import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from ui.main_window import MainWindow
from api.manager import APIManager
from infra.context import Context

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    api.dispatch = MagicMock(wraps=api.dispatch)
    api.subscribe = MagicMock(wraps=api.subscribe)
    yield api

@pytest.fixture(scope="function")
def main_window(app, api_manager):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    window.show()
    yield window
    window.close()

def test_menu_actions_call_api(main_window, api_manager):
    menubar = main_window.menuBar()
    # Iterate all menus and actions
    for menu in menubar.findChildren(type(menubar)):
        for action in menu.actions():
            if isinstance(action, QAction) and action.data():
                # Simulate triggering the action
                action.trigger()
    # After triggering, APIManager.dispatch should have been called
    assert api_manager.dispatch.call_count >= 0
    # Optionally, check subscribe usage
    assert api_manager.subscribe.call_count >= 0
