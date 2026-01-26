
import pytest
from unittest.mock import MagicMock
from api.manager import APIManager
from core.device import Device
from core.selection import SelectionManager
import uuid
from api.actions import register_real_device_actions


@pytest.fixture
def api_manager():
    APIManager.reset()
    # Register real device actions to avoid circular import issues
    register_real_device_actions()
    return APIManager()

@pytest.fixture
def selection_manager():
    mgr = SelectionManager()
    mgr.clear_selection()
    return mgr

def make_device():
    return Device(id=str(uuid.uuid4()), x=0, y=0, rotation=0.0)

def test_context_menu_delete_command(api_manager, selection_manager):
    dev = make_device()
    api_manager.context = MagicMock()
    api_manager.context.harness = MagicMock()
    api_manager.context.harness.devices = [dev]
    api_manager.context.harness.wires = []
    api_manager.context.undo_stack = MagicMock()
    selection_manager.set_selection([dev])
    # Simulate context menu delete
    api_manager.delete()
    # Should push DeleteDeviceCommand to undo stack
    assert api_manager.context.undo_stack.push.call_count == 1
    cmd = api_manager.context.undo_stack.push.call_args[0][0]
    assert cmd.device == dev
    # Simulate undo
    api_manager.context.harness.devices = []
    cmd.undo()
    assert dev in api_manager.context.harness.devices

def test_context_menu_rotate_command(api_manager, selection_manager):
    dev = make_device()
    api_manager.context = MagicMock()
    api_manager.context.harness = MagicMock()
    api_manager.context.harness.devices = [dev]
    api_manager.context.harness.wires = []
    api_manager.context.undo_stack = MagicMock()
    selection_manager.set_selection([dev])
    # Simulate context menu rotate
    api_manager.rotate_cw()
    # Should push RotateDeviceCommand to undo stack
    assert api_manager.context.undo_stack.push.call_count == 1
    cmd = api_manager.context.undo_stack.push.call_args[0][0]
    assert cmd.device == dev
    # Simulate execute/undo
    dev.rotation = 0.0
    cmd.execute()
    assert dev.rotation == 90.0
    cmd.undo()
    assert dev.rotation == 0.0
