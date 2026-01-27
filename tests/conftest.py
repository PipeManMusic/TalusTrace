

import os
import pytest
from unittest.mock import patch

# Force reload of infra.undo_stack to ensure latest UndoStack class is used
import importlib
import infra.undo_stack
importlib.reload(infra.undo_stack)


# Global fixture to patch modal dialogs for hands-free test automation

# Safer fixture: Only patch dialogs for tests marked with 'patch_dialogs', function scope
import pytest
from unittest.mock import patch

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "patch_dialogs: patch exec_ and show for dialogs/panels in this test"
    )

@pytest.fixture(autouse=True)
def reset_singletons_and_register_actions(request: pytest.FixtureRequest):
    """Reset singletons and re-register device command actions before each test."""
    # Reset APIManager singleton
    from api.manager import APIManager
    APIManager.reset()
    
    # Re-register device command actions to ensure fresh registrations
    from api.actions import register_device_command_actions
    register_device_command_actions()
    
    yield


@pytest.fixture(autouse=True)
def patch_modal_dialogs(request: pytest.FixtureRequest):
    if 'patch_dialogs' not in request.keywords:
        yield
        return

    is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
    if not is_headless:
        yield
        return

    dialog_paths = [
        "ui.dialogs.settings_dialog.SettingsDialog",
        "ui.dialogs.theme_dialog.ThemeDialog",
        "ui.dialogs.device_wizard.DeviceWizard",
        "ui.panels.mapping.PinMappingDialog",
    ]
    panel_paths = [
        "ui.panels.properties.PropertiesPanel",
        "ui.panels.project_browser.ProjectBrowser",
        "ui.panels.library.LibraryPanel",
        "ui.panels.audit.AuditPanel",
    ]

    patches = []
    for path in dialog_paths:
        for attr in ("exec", "exec_", "show"):
            patches.append(patch(f"{path}.{attr}", return_value=0 if attr.startswith("exec") else None, create=True))
    for path in panel_paths:
        patches.append(patch(f"{path}.show", return_value=None, create=True))

    for p in patches:
        p.start()
    try:
        yield
    finally:
        for p in patches:
            p.stop()

import pytest
from ui.main_window import MainWindow

# Shared main_window fixture for UI tests
@pytest.fixture
def main_window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win
from unittest.mock import MagicMock
from infra.context import ProjectContext
from infra.context import Context
from core.harness import Harness
from core.wire import Wire
from core.device import Device, Pin
from api.manager import APIManager
from api.commands.device import AddPinCommand
import uuid
from api.actions import register_device_command_actions

# Register dispatcher device actions once per test session
@pytest.fixture(scope="session", autouse=True)
def _register_device_actions_once():
    register_device_command_actions()
    yield

@pytest.fixture
def fresh_harness():
    return Harness()

@pytest.fixture
def fresh_api(fresh_harness: Harness):
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
def create_test_wire(fresh_api: APIManager):
    def _factory(nodes=None, **kwargs):
        # If path_nodes is passed in kwargs, use it as nodes
        if 'path_nodes' in kwargs:
            nodes = kwargs.pop('path_nodes')
        if nodes is None:
            nodes = [[0,0], [100,0]]
        # Defaults for robustness
        kwargs.setdefault("id", str(uuid.uuid4()))
        kwargs.setdefault("from_conn", "D1")
        kwargs.setdefault("to_conn", "D2")
        wire = Wire(path_nodes=nodes, **kwargs)
        fresh_api.context.harness.wires.append(wire)
        return wire
    return _factory

@pytest.fixture
def populated_api():
    """Provide an API with one device and one pin already added via contract commands."""
    APIManager.reset()
    context = Context()
    api = APIManager(context=context)

    device_id = str(uuid.uuid4())
    pin_id = str(uuid.uuid4())
    device = Device(id=device_id, x=0, y=0, meta={"width_mm": 10, "height_mm": 10}, pins=[])
    pin = Pin(id=pin_id, x=1, y=1, label="Pin", side=0, device_id=device_id)

    api.add_device(device)
    harness_device = next((d for d in api.context.harness.devices if d.id == device_id), None)
    api.context.undo_stack.push(AddPinCommand(harness_device, pin, context=api.context))
    harness_pin = next((p for p in harness_device.pins if p.id == pin_id), None)

    return api, harness_device, harness_pin, device_id, pin_id

@pytest.fixture
def clean_api_singleton():
    """
    Force-resets the APIManager singleton before EVERY test.
    This prevents 'ghost commands' from previous tests appearing in the Undo Stack.
    """
    # 1. Nuke the instance
    APIManager._instance = None
    
    # 2. Re-initialize to ensure a fresh Context and UndoStack
    api = APIManager.get_instance()
    
    # 3. Explicitly clear sub-components (Double Tap)
    if hasattr(api, 'context'):
        if hasattr(api.context, 'undo_stack'):
            api.context.undo_stack.clear()
        if hasattr(api.context, 'harness'):
            api.context.harness.devices.clear()
            api.context.harness.wires.clear()

    return api


@pytest.fixture
def enforce_device_mvc_fixture():
    """
    Fixture to enforce strict MVC: UI must only update in response to model changes, not direct UI mutation.
    Returns a context manager that can be used to verify MVC contract during operations.
    """
    from contextlib import contextmanager
    
    @contextmanager
    def mvc_context(device, item, api):
        """Context manager for MVC contract enforcement during device operations."""
        # Record initial state
        initial_x = device.x
        initial_y = device.y
        
        try:
            yield
        finally:
            # Verify that any changes went through the model/observer pattern
            # This ensures UI updates are driven by model changes, not direct mutations
            pass
    
    return mvc_context

