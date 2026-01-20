import os
import pytest
from unittest.mock import patch

# Global fixture to patch modal dialogs for hands-free test automation

# Safer fixture: Only patch dialogs for tests marked with 'patch_dialogs', function scope
import pytest
from unittest.mock import patch

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "patch_dialogs: patch exec_ and show for dialogs/panels in this test"
    )

@pytest.fixture(autouse=True)
def patch_modal_dialogs(request):
    if 'patch_dialogs' not in request.keywords:
        yield
        return
    is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
    if is_headless:
        patches = [
            patch("ui.dialogs.settings_dialog.SettingsDialog.exec_", return_value=0),
            patch("ui.dialogs.theme_dialog.ThemeDialog.exec_", return_value=0),
            patch("ui.dialogs.device_wizard.DeviceWizard.exec_", return_value=0),
            patch("ui.panels.mapping.PinMappingDialog.exec_", return_value=0),
            patch("ui.dialogs.settings_dialog.SettingsDialog.show", return_value=None),
            patch("ui.dialogs.theme_dialog.ThemeDialog.show", return_value=None),
            patch("ui.dialogs.device_wizard.DeviceWizard.show", return_value=None),
            patch("ui.panels.mapping.PinMappingDialog.show", return_value=None),
            patch("ui.panels.properties.PropertiesPanel.show", return_value=None),
            patch("ui.panels.project_browser.ProjectBrowser.show", return_value=None),
            patch("ui.panels.library.LibraryPanel.show", return_value=None),
            patch("ui.panels.audit.AuditPanel.show", return_value=None),
        ]
        for p in patches:
            p.start()
        yield
        for p in patches:
            p.stop()
    else:
        yield

import pytest
from ui.main_window import MainWindow

# Shared main_window fixture for UI tests
@pytest.fixture
def main_window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win
import pytest
import sys
import importlib

@pytest.fixture
def enforce_device_mvc_fixture():
    # Import context manager from mvc_enforce.py
    sys.path.append('.')
    mvc_enforce = importlib.import_module('tests.mvc_enforce')
    return mvc_enforce.enforce_device_mvc
from unittest.mock import MagicMock
from infra.context import ProjectContext
from core.harness import Harness
from core.wire import Wire
from api.manager import APIManager

@pytest.fixture
def fresh_harness():
    return Harness()

@pytest.fixture
def fresh_api(fresh_harness):
    # Reset Singleton
    APIManager._instance = None
    
    # Setup Headless API
    api = APIManager()
    api.context = ProjectContext()
    api.context.harness = fresh_harness
    
    # Mock UI dependencies (Scene/View) so logic tests don't crash
    api.scene = MagicMock()
    api.view = MagicMock()
    api.view.transform.return_value = MagicMock() 
    
    return api

@pytest.fixture
def create_test_wire(fresh_api):
    def _factory(nodes=None, **kwargs):
        # If path_nodes is passed in kwargs, use it as nodes
        if 'path_nodes' in kwargs:
            nodes = kwargs.pop('path_nodes')
        if nodes is None:
            nodes = [[0,0], [100,0]]
        # Defaults for robustness
        kwargs.setdefault("id", "W_TEST")
        kwargs.setdefault("from_conn", "D1")
        kwargs.setdefault("to_conn", "D2")
        wire = Wire(path_nodes=nodes, **kwargs)
        fresh_api.context.harness.wires.append(wire)
        return wire
    return _factory
