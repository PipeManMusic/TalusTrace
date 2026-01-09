import pytest
from api.actions import registry
from api.manager import APIManager
import api.commands  # Critical: Forces action registration
from core.device import Device
from core.selection import SelectionManager

@pytest.fixture(autouse=True)
def setup_test_env():
    api = APIManager.get_instance()
    api.context.harness.devices.clear()
    api.context.undo_stack.clear()
    SelectionManager().current_selection_ids.clear()
    yield

def test_delete_logic_functional():
    api = APIManager.get_instance()
    dev = Device(id="TargetDev", x=10, y=10)
    api.context.harness.devices.append(dev)
    
    # SelectionManager must have the ID and selected_models for the command to find it
    sel = SelectionManager()
    sel.current_selection_ids.add("TargetDev")
    sel.selected_models = [dev]
    
    registry.execute("edit.delete")
    assert all(d.id != "TargetDev" for d in api.context.harness.devices)