import pytest
from core.device import Device
from core.pin import Pin

# Dummy schema for pin metadata
def get_pin_with_metadata():
    import uuid
    pin = Pin(id=str(uuid.uuid4()), x=0, y=0, signal="A", meta={"custom_field": "value", "_type": "test_pin"})
    return pin

def test_pin_metadata_preserved():
    pin = get_pin_with_metadata()
    # Simulate API returning pin with metadata
    assert hasattr(pin, 'meta')
    assert pin.meta["custom_field"] == "value"
    assert pin.meta["_type"] == "test_pin"

    # Simulate serialization/deserialization round-trip
    data = pin.to_dict()
    pin2 = Pin.from_dict(data)
    assert pin2.meta["custom_field"] == "value"
    assert pin2.meta["_type"] == "test_pin"
