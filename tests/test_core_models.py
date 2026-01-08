import pytest
from core.device import Device, Pin
from core.wire import Wire

def test_device_initialization_with_pins():
    """Verify a Device can contain Pins and maintains mm-based position."""
    test_pin = Pin(id="p1", meta={"name": "Source"})
    device = Device(
        id="dev_001",
        label="BATT_CONN",
        x=100.0,
        y=250.0,
        pins=[test_pin]
    )
    assert device.id == "dev_001"
    assert device.x == 100.0
    assert device.y == 250.0
    assert len(device.pins) == 1
    assert device.pins[0].id == "p1"

def test_device_rotation_validation():
    """Ensure rotation is stored as a float."""
    device = Device(id="d1", rotation=90.0)
    assert isinstance(device.rotation, float)
    assert device.rotation == 90.0

def test_device_revision_initialization():
    """Verify default revision for optimistic locking."""
    device = Device(id="d2")
    assert device.revision == 0

def test_wire_initialization():
    """Verify basic Wire model initialization."""
    wire = Wire(
        id="w1",
        from_conn="d1.p1",
        to_conn="d2.p1",
        path_nodes=[[0.0, 0.0], [10.0, 10.0]]
    )
    assert wire.id == "w1"
    assert wire.path_nodes == [[0.0, 0.0], [10.0, 10.0]]