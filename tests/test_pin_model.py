import pytest
from core.pin import Pin
from core.enums import Side

def test_pin_schema_and_serialization():
    # Create a pin
    pin = Pin(
        id="44444444-4444-4444-4444-444444444444",
        label=None,  # Should default to id
        side=Side.TOP,
        x=5.0,
        y=10.0,
        head=[1.0, 2.0],
        tail=[3.0, 4.0],
        device_id="dev-001",
        meta={"foo": "bar"}
    )
    # Validate schema
    assert pin.id == "44444444-4444-4444-4444-444444444444"
    assert pin.label == "44444444-4444-4444-4444-444444444444"  # Defaults to id
    assert pin.side == Side.TOP
    assert pin.x == 5.0
    assert pin.head == [1.0, 2.0]
    assert pin.device_id == "dev-001"
    # Test serialization
    data = pin.to_dict()
    assert data["id"] == "44444444-4444-4444-4444-444444444444"
    assert data["side"] == "top"
    # Test deserialization
    pin2 = Pin.from_dict(data)
    assert pin2 == pin
    # Test mm float storage
    assert isinstance(pin.x, float)
    assert isinstance(pin.head[0], float)
