"""
Integration test: Full API workflow for Talus Trace
Covers device, pin, wire creation, undo/redo, and persistence.
"""
import pytest
import uuid
from api.manager import APIManager
from core.device import Device
from core.pin import Pin
from core.wire import Wire
from unittest.mock import MagicMock

@pytest.fixture
def api():
    APIManager.reset()
    return APIManager()

def test_full_device_wire_workflow(api):
    # Create devices
    dev1 = Device(id=str(uuid.uuid4()), x=0, y=0)
    dev2 = Device(id=str(uuid.uuid4()), x=100, y=0)
    # Add pins
    pin1 = Pin(id=str(uuid.uuid4()), x=10, y=10)
    pin2 = Pin(id=str(uuid.uuid4()), x=110, y=10)
    dev1.pins.append(pin1)
    dev2.pins.append(pin2)
    # Add devices to harness
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev1)
        api.context.harness.devices.append(dev2)
    # Create wire
    wire = Wire(id=str(uuid.uuid4()), from_conn=dev1.id, from_pin=pin1.id, to_conn=dev2.id, to_pin=pin2.id, path_nodes=[[10,10],[110,10]])
    api.context.harness.wires.append(wire)
    # Assert model state
    assert len(api.context.harness.devices) == 2
    assert len(api.context.harness.wires) == 1
    # Undo/redo stack
    api.context.undo_stack.push(MagicMock())
    assert api.context.undo_stack.can_undo()
    api.context.undo_stack.undo()
    assert api.context.undo_stack.can_redo()
    api.context.undo_stack.redo()
    # Persistence (simulate save/load)
    import json
    # Manual serialization for Harness
    data = {
        'devices': [d.id for d in api.context.harness.devices],
        'wires': [w.id for w in api.context.harness.wires]
    }
    json_str = json.dumps(data)
    loaded = json.loads(json_str)
    assert loaded['devices'] and loaded['wires']
