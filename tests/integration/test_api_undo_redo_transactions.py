"""
Integration test: Undo/Redo transaction grouping and edge cases for Talus Trace API
Covers grouped transactions, multiple undos/redos, and empty stack edge cases.
"""
import pytest
import uuid
from api.manager import APIManager
from core.device import Device
from core.pin import Pin
from core.harness import DeviceList
from unittest.mock import MagicMock

@pytest.fixture
def api():
    APIManager.reset()
    return APIManager()

def test_transaction_grouping_and_edge_cases(api):
    # Setup devices
    dev1 = Device(id=str(uuid.uuid4()), x=0, y=0)
    dev2 = Device(id=str(uuid.uuid4()), x=100, y=0)
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev1)
        api.context.harness.devices.append(dev2)
    # Begin transaction
    stack = api.context.undo_stack
    stack.begin_transaction("Add two devices")
    stack.push(MagicMock())
    stack.push(MagicMock())
    stack.end_transaction()
    # Only one transaction should be on stack
    assert len(stack) == 1
    # Undo transaction
    stack.undo()
    assert stack.can_redo()
    # Redo transaction
    stack.redo()
    assert stack.can_undo()
    # Edge case: undo until empty
    stack.undo()
    assert not stack.can_undo()
    # Redo until empty
    stack.redo()
    assert not stack.can_redo()
    # Try undo/redo on empty stack (should not error)
    stack.undo()
    stack.redo()
