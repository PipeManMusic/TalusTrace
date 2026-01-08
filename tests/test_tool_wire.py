import pytest
from core.harness import Harness
from core.device import Device, Pin
# Target Implementation: tools/wire_tool.py
from tools.wire_tool import WireTool, WireToolState

def test_wire_tool_state_machine():
    harness = Harness()
    d1 = Device(id="D1", pins=[Pin(id="P1")])
    harness.add_device(d1)
    
    tool = WireTool(harness)
    assert tool.state == WireToolState.IDLE
    
    # 1. Click Pin -> Start Dragging
    tool.on_click(device_id="D1", pin_id="P1")
    assert tool.state == WireToolState.DRAGGING
    assert tool.start_pin == "P1"
    
    # 2. Click Empty Space -> Ignore (Enforce Pin-to-Pin)
    tool.on_click(device_id=None, pin_id=None)
    assert len(harness.wires) == 0
    
    # 3. Click Pin 2 -> Create Wire
    d2 = Device(id="D2", pins=[Pin(id="P2")])
    harness.add_device(d2)
    tool.on_click(device_id="D2", pin_id="P2")
    
    assert tool.state == WireToolState.IDLE
    assert len(harness.wires) == 1