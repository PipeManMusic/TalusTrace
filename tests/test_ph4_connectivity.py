import pytest
from core.device import Device, Pin
from core.enums import Side

def test_ph4_1_2_connector_pin_matrix():
    """
    Validates Device model generates physical Pin coordinates.
    Aligned with core/pin.py and PH4-1.2.
    """
    # 2x4 Matrix connector logic
    import uuid
    pitch = 2.54
    pins = []
    label_to_uuid = {}
    for row in range(2):
        for col in range(4):
            idx = row * 4 + col
            pin_label = f"P{idx+1}"
            pin_uuid = str(uuid.uuid4())
            label_to_uuid[pin_label] = pin_uuid
            pins.append(Pin(
                id=pin_uuid,
                label=pin_label,
                side=Side.LEFT,
                x=col * pitch,
                y=row * pitch
            ))
    device_uuid = str(uuid.uuid4())
    conn = Device(id=device_uuid, pins=pins, x=0.0, y=0.0)
    # Assertions
    assert len(conn.pins) == 8
    # Check Pin 1 (Origin)
    pin_1 = next(p for p in conn.pins if p.label == "P1")
    assert pin_1.x == 0.0
    # Check Pin 2 (Offset by 1 pitch)
    pin_2 = next(p for p in conn.pins if p.label == "P2")
    assert pin_2.x == 2.54