import pytest
from pydantic import ValidationError
from core.models import Pin, Device

def test_device_initialization_with_pins():
    """Verify a Device can contain Pins and maintains mm-based position."""
    import uuid
    pin_id = str(uuid.uuid4())
    device_id = str(uuid.uuid4())
    test_pin = Pin(id=pin_id)
    device = Device(id=device_id, pins=[test_pin], x=100.0, y=250.0)
    assert device.id == device_id
    assert device.x == 100.0
    assert device.y == 250.0
    assert len(device.pins) == 1
    assert device.pins[0].id == pin_id
    assert device.is_ghost is False  # Default state

def test_device_rotation_validation():
    """Ensure rotation is stored as a float."""
    import uuid
    device_id = str(uuid.uuid4())
    device = Device(id=device_id, name="R1", rotation=90.0)
    assert isinstance(device.rotation, float)

def test_device_revision_initialization():
    """Verify default revision for optimistic locking."""
    import uuid
    device_id = str(uuid.uuid4())
    device = Device(id=device_id, name="R2")
    assert device.revision == 0