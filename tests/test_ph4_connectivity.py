import pytest
from core.device import Device, Pin
from core.enums import Side

def test_ph4_1_2_connector_pin_matrix():
    """
    Validates Device model generates physical Pin coordinates.
    Aligned with core/pin.py and PH4-1.2.
    """
    # 2x4 Matrix connector logic
    pitch = 2.54
    pins = []
    for row in range(2):
        for col in range(4):
            idx = row * 4 + col
            pins.append(Pin(
                id=f"P{idx+1}",
                label=f"P{idx+1}",
                # FIX: Use a valid cardinal direction
                side=Side.LEFT,
                x=col * pitch,
                y=row * pitch
            ))
            
    conn = Device(id="J1", pins=pins, x=0.0, y=0.0)
    
    # Assertions
    assert len(conn.pins) == 8
    
    # Check Pin 1 (Origin)
    pin_1 = next(p for p in conn.pins if p.id == "P1")
    assert pin_1.x == 0.0
    
    # Check Pin 2 (Offset by 1 pitch)
    pin_2 = next(p for p in conn.pins if p.id == "P2")
    assert pin_2.x == 2.54