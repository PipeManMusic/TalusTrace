import pytest
from core.device import Device, Pin
from core.wire import Wire

def test_device_initialization_with_pins():
    """Verify a Device can contain Pins and maintains mm-based position."""
    import uuid
    pin_id = str(uuid.uuid4())
    device_id = str(uuid.uuid4())
    test_pin = Pin(id=pin_id, meta={"name": "Source"})
    device = Device(
        id=device_id,
        label="BATT_CONN",
        x=100.0,
        y=250.0,
        pins=[test_pin]
    )
    assert device.id == device_id
    assert device.x == 100.0
    assert device.y == 250.0
    assert len(device.pins) == 1
    assert device.pins[0].id == pin_id

def test_device_rotation_validation():
    """Ensure rotation is stored as a float."""
    import uuid
    device_id = str(uuid.uuid4())
    device = Device(id=device_id, rotation=90.0)
    assert isinstance(device.rotation, float)
    assert device.rotation == 90.0

def test_device_revision_initialization():
    """Verify default revision for optimistic locking."""
    import uuid
    device_id = str(uuid.uuid4())
    device = Device(id=device_id)
    assert device.revision == 0

def test_wire_initialization():
    """Verify basic Wire model initialization."""
    import uuid
    wire = Wire(
        id=str(uuid.uuid4()),
        from_conn="d1.p1",
        to_conn="d2.p1",
        path_nodes=[[0.0, 0.0], [10.0, 10.0]]
    )
    import re
    uuid_regex = re.compile(r"^[a-f0-9\-]{36}$", re.I)
    assert uuid_regex.match(wire.id)
    assert wire.path_nodes == [[0.0, 0.0], [10.0, 10.0]]