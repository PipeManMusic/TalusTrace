import pytest
from api.manager import APIManager
from core.pin import Pin

def test_add_wire_undo_compliance():
    """
    Verifies that APIManager.add_wire respects the Command Pattern.
    
    Current Behavior (BROKEN):
    1. add_wire() appends directly to the list.
    2. Pushes a "Mock" command where undo() is 'pass'.
    3. Calling undo() does nothing, so the wire stays. -> ASSERTION ERROR
    
    Expected Behavior (FIXED):
    1. add_wire() pushes a real AddWireCommand.
    2. The command executes and adds the wire.
    3. Calling undo() removes the wire. -> SUCCESS
    """
    # 1. Setup: Reset API to a clean state
    APIManager.reset()
    api = APIManager.get_instance()
    
    # Ensure harness is empty
    api.context.harness.wires.clear()
    assert len(api.context.harness.wires) == 0
    
    # Create dummy pins for the connection
    pin1 = Pin(id="P1", x=0, y=0, device_id="D1")
    pin2 = Pin(id="P2", x=10, y=10, device_id="D2")
    
    # 2. Action: Create the wire
    api.add_wire(pin1, pin2)
    
    # Verify it was added (Phases 3 & 4 Execution)
    assert len(api.context.harness.wires) == 1
    
    # 3. Action: Undo
    api.context.undo_stack.undo()
    
    # 4. Critical Assertion: The wire should be gone
    # This will FAIL currently because the Mock Command has no undo logic.
    assert len(api.context.harness.wires) == 0, \
        "VIOLATION: Undo failed! The wire remains in the model, proving direct mutation occurred."
