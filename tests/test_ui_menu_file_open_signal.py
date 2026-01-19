import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
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
    yield api

@pytest.fixture(scope="function")
def main_window(app, api_manager):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    window.show()
    yield window
    window.close()

@pytest.mark.usefixtures("app", "main_window")
def test_file_open_menu_action_missing_signal(qtbot, main_window):
    menubar = main_window.menuBar()
    file_menu = None
    for action in menubar.actions():
        menu = action.menu()
        if menu and menu.title() == "File":
            file_menu = menu
            break
    assert file_menu is not None, "File menu not found"
    file_open_action = None
    for action in file_menu.actions():
        if action.data() == "file.open":
            file_open_action = action
            break
    assert file_open_action is not None, "file.open action not found"
    with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
        file_open_action.trigger()
        if not mock_dialog.called:
            pytest.fail("file.open menu action does NOT open the file dialog. Signal connection is missing.")
