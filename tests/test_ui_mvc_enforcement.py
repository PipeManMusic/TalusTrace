import pytest
from unittest.mock import MagicMock
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
    # Spy on dispatch and subscribe
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

@pytest.fixture(scope="function")
def harness_canvas(main_window):
    canvas = main_window.canvas
    yield canvas

# Example enforcement test: UI must only communicate via APIManager
# This can be expanded for each panel, dialog, and item

def test_mainwindow_uses_api_manager(main_window, api_manager):
    # Simulate a UI action that should dispatch via APIManager
    main_window.update_title(is_dirty=True)
    # Check that APIManager was not bypassed for model changes
    assert api_manager.dispatch.call_count == 0
    # Panels should subscribe via APIManager
    for panel_name in ["project_browser", "library_panel", "properties_panel", "audit_panel"]:
        panel = getattr(main_window, panel_name, None)
        if panel:
            assert api_manager.subscribe.called

# Expand with similar tests for dialogs, panels, and canvas items
