"""
Integration test: Edge cases and stress tests for Talus Trace API
Covers large batch operations, repeated undo/redo, invalid input, and empty model edge cases.
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

def test_empty_model_undo_redo(api):
    # Undo/redo on empty stack should not error
    api.context.undo_stack.undo()
    api.context.undo_stack.redo()
    assert not api.context.undo_stack.can_undo()
    assert not api.context.undo_stack.can_redo()

def test_invalid_device_id(api):
    # Try to create device with invalid UUID
    with pytest.raises(ValueError):
        Device(id="not-a-uuid", x=0, y=0)

def test_large_batch_device_creation(api):
    # Stress test: create 1000 devices
    ids = set()
    with DeviceList.test_bypass():
        for _ in range(1000):
            dev = Device(id=str(uuid.uuid4()), x=0, y=0)
            api.context.harness.devices.append(dev)
            ids.add(dev.id)
    assert len(api.context.harness.devices) == 1000
    assert len(ids) == 1000

def test_repeated_undo_redo(api):
    # Stress test: push 50 commands, undo/redo all
    stack = api.context.undo_stack
    for _ in range(50):
        stack.push(MagicMock())
    for _ in range(50):
        stack.undo()
    assert not stack.can_undo()
    for _ in range(50):
        stack.redo()
    assert not stack.can_redo()

def test_wire_with_missing_pin(api):
    # Edge case: wire references missing pin
    dev1 = Device(id=str(uuid.uuid4()), x=0, y=0)
    dev2 = Device(id=str(uuid.uuid4()), x=100, y=0)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev1)
        api.context.harness.devices.append(dev2)
    # Pin not added to device
    wire = Wire(id=str(uuid.uuid4()), from_conn=dev1.id, from_pin="missing-pin", to_conn=dev2.id, to_pin="missing-pin", path_nodes=[[0,0],[100,0]])
    api.context.harness.wires.append(wire)
    assert wire.from_pin == "missing-pin"
    assert wire.to_pin == "missing-pin"
