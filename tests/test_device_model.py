import pytest

from core.device import Device
from core.pin import Pin
from core.enums import Side


def test_device_schema_and_serialization():
    # Create a device with pins
    import uuid
    device = Device(
        id=str(uuid.uuid4()),
        label="Test Device",
        pins=[
            Pin(id=str(uuid.uuid4()), x=1.0, y=2.0),
            Pin(id=str(uuid.uuid4()), x=3.0, y=4.0, side=Side.RIGHT),
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
    import uuid
    assert uuid.UUID(device.id)
    assert uuid.UUID(device.pins[0].id)
    assert device.is_ghost is True
    assert device.library_id == "lib-xyz"
    # Test serialization
    data = device.to_dict()
    assert uuid.UUID(data["id"])
    assert uuid.UUID(data["pins"][0]["id"])
    # Test deserialization
    device2 = Device.from_dict(data)
    assert device2 == device
    # Test mm float storage
    assert isinstance(device.x, float)
    assert isinstance(device.pins[0].x, float)
