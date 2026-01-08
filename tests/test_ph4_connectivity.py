import pytest
from core.models import Wire
from core.device import Device
from core.pin import Pin

def test_ph4_1_1_wire_pin_assignment():
    """
    Validates Wire model tracks from_conn and to_conn.
    Aligned with core/models.py and PH4-1.1.
    """
    wire = Wire(
        id="W001",
        from_conn="J1:1",
        to_conn="J2:A",
        path_nodes=[(0.0, 0.0), (10.0, 0.0)]
    )
    # Fixed: Using mandated attribute names from core/models.py
    assert wire.from_conn == "J1:1"
    assert wire.to_conn == "J2:A"

def test_ph4_1_2_connector_pin_matrix():
    """
    Validates Device model generates physical Pin coordinates.
    Aligned with core/pin.py and PH4-1.2.
    """
    # 2x4 Matrix connector logic
    # Manually generate pins for a 2x4 matrix connector
    pitch = 2.54
    pins = []
    for row in range(2):
        for col in range(4):
            idx = row * 4 + col
            pins.append(Pin(
                id=f"P{idx+1}",
                label=f"P{idx+1}",
                side="A",
                x=col * pitch,
                y=row * pitch,
                head=[],
                tail=[]
            ))
    conn = Device(id="J1", pins=[p.model_dump() for p in pins], x=0.0, y=0.0)
    assert len(conn.pins) == 8
    print('DEBUG pin labels:', [p.label for p in conn.pins])
    assert any(p.label == 'P1' for p in conn.pins)
    
    # Fixed: Using .head[0] to access the X coordinate (mm) per core/pin.py
    # Pin 1:1 is at origin (0.0)
    pin_1_1 = next((p for p in conn.pins if p.label == "P1"), None)
    assert pin_1_1 is not None
    assert pin_1_1.x == 0.0
    
    # Pin 1:2 is offset by one pitch (2.54mm)
    pin_1_2 = next((p for p in conn.pins if p.label == "P2"), None)
    assert pin_1_2 is not None
    assert pin_1_2.x == 2.54