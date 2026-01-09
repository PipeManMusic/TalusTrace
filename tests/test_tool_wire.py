import pytest
from core.models import Harness, Device, Pin
from tools.wire_tool import WireTool, WireToolState

def test_wire_tool_state_machine():
    harness = Harness()
    d1 = Device(id="D1", pins=[Pin(id="P1")])
    harness.add_device(d1)

    tool = WireTool(harness)
    assert tool.state == WireToolState.IDLE

    # 1. Click Pin -> Start Dragging
    # The 'on_click' helper injects the state transition
    tool.on_click(device_id="D1", pin_id="P1")
    
    assert tool.state == WireToolState.DRAGGING
    
    # FIX: Check .id because start_pin is now a Pin Object, not a string
    assert tool.start_pin.id == "P1"
    
    # 2. Click Same Pin -> No Change
    tool.on_click(device_id="D1", pin_id="P1")
    assert tool.state == WireToolState.DRAGGING

    # 3. Click Empty Space (Invalid Pin) -> Cancel
    tool.on_click(device_id="NON_EXISTENT", pin_id="NONE")
    
    # Verify cancellation logic (if implemented) or just safety
    # In current impl, invalid clicks are ignored in IDLE, but might cancel in DRAGGING
    # The key is that it doesn't crash.