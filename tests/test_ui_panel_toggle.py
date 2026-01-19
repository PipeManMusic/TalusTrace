import pytest
from PySide6.QtWidgets import QApplication, QDockWidget
from ui.main_window import MainWindow
from api.manager import APIManager
from infra.context import Context
from api.actions import registry

PANEL_COMMANDS = {
    "view.toggle_project_browser": "ProjectBrowserDock",
    "view.toggle_property_panel": "PropertiesPanelDock",
    "view.toggle_library": "LibraryPanelDock",
    "view.toggle_audit_panel": "AuditPanelDock",
}

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

def test_panel_toggle_commands(main_window):
    for cmd, panel_name in PANEL_COMMANDS.items():
        # Find the panel dock widget by name
        dock = main_window.findChild(QDockWidget, panel_name)
        assert dock is not None, f"Panel {panel_name} not found in main window."
        # Toggle panel (simulate command)
        initial_visible = dock.isVisible()
        registry.execute(cmd, main_window.api.context)
        # After toggle, visibility should change
        assert dock.isVisible() != initial_visible, f"Panel {panel_name} did not toggle visibility after {cmd}."
