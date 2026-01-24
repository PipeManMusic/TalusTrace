"""
Integration test: Tool API contract for Talus Trace
Covers activation, device placement, wire creation, and undo/redo via tool manager.
"""
import pytest
import uuid
from api.manager import APIManager
from tools.placement_tool import PlacementTool
from tools.wire_tool import WireTool
from core.device import Device
from core.pin import Pin
from core.harness import DeviceList
from unittest.mock import MagicMock

@pytest.fixture
def api():
    APIManager.reset()
    return APIManager()

def test_tool_activation_and_wire(api):
    # Activate placement tool and add device
    placement_tool = PlacementTool()
    placement_tool.api = api
    dev_id = str(uuid.uuid4())
    meta = {'_type': 'generic'}
    device = Device(id=dev_id, x=0, y=0, meta=meta)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    # Activate wire tool and add wire
    wire_tool = WireTool()
    wire_tool._api_instance = api
    pin1 = Pin(id=str(uuid.uuid4()), x=10, y=10)
    device.pins.append(pin1)
    dev2 = Device(id=str(uuid.uuid4()), x=100, y=0, meta=meta)
    pin2 = Pin(id=str(uuid.uuid4()), x=110, y=10)
    dev2.pins.append(pin2)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev2)
    wire_tool._create_wire(device, pin1, dev2, pin2)
    # Assert wire created
    assert len(api.context.harness.wires) == 1
    # Undo/redo
    api.context.undo_stack.push(MagicMock())
    assert api.context.undo_stack.can_undo()
    api.context.undo_stack.undo()
    assert api.context.undo_stack.can_redo()
    api.context.undo_stack.redo()
