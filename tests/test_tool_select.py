import pytest
from PySide6.QtCore import QRectF, QPointF
from tools.select_tool import SelectTool
from core.models import Harness, Device, Wire

# --- Marquee Selection Tests ---
def test_marquee_selection_logic():
    """PH5-INTER.1: Validate Enclosing vs Crossing selection logic."""
    harness = Harness()
    # Device at (10, 10) 20x20 -> Bounds (10, 10) to (30, 30)
    d1 = Device(id="D1", x=10.0, y=10.0)
    harness.add_device(d1)
    
    tool = SelectTool()
    tool._get_harness = lambda: harness 
    
    # 1. Enclosing (0,0,50,50) -> Fully contains D1
    enclosing_rect = QRectF(0, 0, 50, 50) 
    hits = tool._calculate_marquee_hits(enclosing_rect, crossing=False)
    assert d1 in hits

    # 2. Partial (20,20,20,20) -> Clips D1
    partial_rect = QRectF(20, 20, 20, 20)
    
    # Enclosing Mode -> Should FAIL
    hits_strict = tool._calculate_marquee_hits(partial_rect, crossing=False)
    assert d1 not in hits_strict

    # Crossing Mode -> Should PASS
    hits_loose = tool._calculate_marquee_hits(partial_rect, crossing=True)
    assert d1 in hits_loose

# --- Elbow / Bend Point Tests ---
def test_add_bend_point_action():
    """PH5-WIRE.1: SelectTool should support adding bend points to wires."""
    harness = Harness()
    wire = Wire(id="W1", from_conn="D1", to_conn="D2")
    # Wire goes from (0,0) to (100,100) implicitly if D1/D2 coords generic
    harness.wires.append(wire)
    
    tool = SelectTool()
    tool._get_harness = lambda: harness
    
    # 1. Simulate "Add Point" Context Action
    # This method needs to be implemented in SelectTool
    tool.add_bend_point(wire_id="W1", location=(50.0, 50.0))
    
    # 2. Verify Model Update
    assert len(wire.points) == 1
    assert wire.points[0] == (50.0, 50.0)

def test_wire_hit_testing():
    """PH5-WIRE.1: SelectTool should detect clicks on thin wires."""
    harness = Harness()
    # Horizontal wire from (0,10) to (100,10)
    d1 = Device(id="D1", x=0.0, y=10.0) 
    d2 = Device(id="D2", x=100.0, y=10.0)
    # Note: Real logic might need fully resolved coords, 
    # but hit_test_wire usually interpolates between endpoints.
    
    wire = Wire(id="W1", from_conn="D1", to_conn="D2")
    harness.devices.append(d1)
    harness.devices.append(d2)
    harness.wires.append(wire)
    tool = SelectTool()
    tool._get_harness = lambda: harness

    # Click EXACTLY on the line
    assert tool.hit_test_wire(QPointF(50, 10), tolerance=5.0) is True

    # Click NEAR the line (Tolerance check)
    assert tool.hit_test_wire(QPointF(50, 12), tolerance=5.0) is True

    # Click TOO FAR
    assert tool.hit_test_wire(QPointF(50, 20), tolerance=5.0) is False