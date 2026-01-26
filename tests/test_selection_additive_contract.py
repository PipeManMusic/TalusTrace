import pytest
from unittest.mock import MagicMock
from api.manager import APIManager
from core.device import Device
from core.selection import SelectionManager
import uuid

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

@pytest.fixture
def selection_manager():
    mgr = SelectionManager()
    mgr.clear_selection()
    return mgr

def test_additive_selection_adds_to_set(api_manager, selection_manager):
    # Setup two devices with valid UUIDs
    dev1_id = str(uuid.uuid4())
    dev2_id = str(uuid.uuid4())
    dev1 = Device(id=dev1_id)
    dev2 = Device(id=dev2_id)
    api_manager.context = MagicMock()
    api_manager.context.harness = MagicMock()
    api_manager.context.harness.devices = [dev1, dev2]
    api_manager.context.harness.wires = []
    # Select dev1
    api_manager.select([dev1_id])
    assert selection_manager.selected_models == [dev1]
    # Add dev2 (additive)
    api_manager.select([dev2_id], additive=True)
    # Both should be selected, in order
    assert selection_manager.selected_models == [dev1, dev2]

def test_blank_canvas_clears_selection(api_manager, selection_manager):
    dev1_id = str(uuid.uuid4())
    dev1 = Device(id=dev1_id)
    api_manager.context = MagicMock()
    api_manager.context.harness = MagicMock()
    api_manager.context.harness.devices = [dev1]
    api_manager.context.harness.wires = []
    # Select dev1
    api_manager.select([dev1_id])
    assert selection_manager.selected_models == [dev1]
    # Simulate blank canvas click (deselect_all)
    api_manager.deselect_all = getattr(api_manager, "clear_selection", lambda: None)
    api_manager.clear_selection()
    assert selection_manager.selected_models == []
