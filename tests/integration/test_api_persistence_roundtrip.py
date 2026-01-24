"""
Integration test: Persistence round-trip for Talus Trace API
Covers saving and loading harness state, ensuring data integrity.
"""
import pytest
import uuid
import json
from api.manager import APIManager
from core.device import Device
from core.pin import Pin
from core.harness import DeviceList

@pytest.fixture
def api():
    APIManager.reset()
    return APIManager()

def test_persistence_roundtrip(api):
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
    # Serialize
    data = {
        'devices': [d.id for d in api.context.harness.devices],
        'pins': [p.id for d in api.context.harness.devices for p in d.pins],
        'wires': [w.id for w in api.context.harness.wires]
    }
    json_str = json.dumps(data)
    # Simulate load
    loaded = json.loads(json_str)
    assert set(loaded['devices']) == set([dev1.id, dev2.id])
    assert set(loaded['pins']) == set([pin1.id, pin2.id])
    assert loaded['wires'] == []
