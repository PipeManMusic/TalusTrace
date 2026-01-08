import pytest
from core.device import Device
from core.pin import Pin


def test_device_schema_and_serialization():
    # Create a device with pins
    device = Device(
        id="dev-001",
        label="Test Device",
        pins=[
            Pin(id="P1", x=1.0, y=2.0),
            Pin(id="P2", x=3.0, y=4.0, side="right"),
        ],
        x=10.0,
        y=20.0,
        rotation=90.0,
        revision=2,
        is_ghost=True,
        library_id="lib-xyz",
        meta={"foo": "bar"}
    )
    # Validate schema
    assert device.id == "dev-001"
    assert device.pins[0].id == "P1"
    assert device.is_ghost is True
    assert device.library_id == "lib-xyz"
    # Test serialization
    data = device.model_dump()
    assert data["id"] == "dev-001"
    assert data["pins"][0]["id"] == "P1"
    # Test deserialization
    device2 = Device.model_validate(data)
    assert device2 == device
    # Test mm float storage
    assert isinstance(device.x, float)
    assert isinstance(device.pins[0].x, float)
