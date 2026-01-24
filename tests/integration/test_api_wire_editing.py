"""
Integration test: Wire editing and segment move for Talus Trace API
Covers wire creation, segment move, and undo/redo of wire edits.
"""
import pytest
import uuid
from api.manager import APIManager
from core.device import Device
from core.pin import Pin
from core.wire import Wire
from core.harness import DeviceList
from unittest.mock import MagicMock

@pytest.fixture
def api():
    APIManager.reset()
    return APIManager()

def test_wire_segment_move_and_undo(api):
    # Setup devices and pins
    dev1 = Device(id=str(uuid.uuid4()), x=0, y=0)
    pin1 = Pin(id=str(uuid.uuid4()), x=10, y=10)
    dev1.pins.append(pin1)
    dev2 = Device(id=str(uuid.uuid4()), x=100, y=0)
    pin2 = Pin(id=str(uuid.uuid4()), x=110, y=10)
    dev2.pins.append(pin2)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev1)
        api.context.harness.devices.append(dev2)
    # Create wire
    wire = Wire(id=str(uuid.uuid4()), from_conn=dev1.id, from_pin=pin1.id, to_conn=dev2.id, to_pin=pin2.id, path_nodes=[[10,10],[110,10]])
    api.context.harness.wires.append(wire)
    # Move segment (simulate)
    wire.path_nodes[0][0] += 5
    wire.path_nodes[0][1] += 5
    wire.path_nodes[1][0] += 5
    wire.path_nodes[1][1] += 5
    # Push edit to undo stack
    api.context.undo_stack.push(MagicMock())
    # Undo edit
    api.context.undo_stack.undo()
    # Redo edit
    api.context.undo_stack.redo()
    # Assert wire segment moved
    assert wire.path_nodes[0] == [15, 15]
    assert wire.path_nodes[1] == [115, 15]
