import pytest
from pydantic import ValidationError
from core.models import Pin, Device

def test_device_initialization_with_pins():
    """Verify a Device can contain Pins and maintains mm-based position."""
    test_pin = Pin(
        id="p1",
        head=(5.0, 5.0),
        tail=(0.0, 0.0),
        name="Source"
    )
    
    device = Device(
        id="dev_001",
        name="BATT_CONN",
        pos=(100.0, 250.0),
        pins=[test_pin]
    )
    
    assert device.id == "dev_001"
    assert device.pos == (100.0, 250.0)
    assert len(device.pins) == 1
    assert device.pins[0].id == "p1"
    assert device.is_ghost is True  # Default state

def test_device_rotation_validation():
    """Ensure rotation is stored as a float."""
    device = Device(id="d1", name="R1", rotation=90.0)
    assert isinstance(device.rotation, float)

def test_device_revision_initialization():
    """Verify default revision for optimistic locking."""
    device = Device(id="d2", name="R2")
    assert device.revision == 0

def test_invalid_device_coordinates():
    """Reject non-float coordinates in Device position."""
    with pytest.raises(ValidationError):
        Device(id="err", name="Fail", pos=("x", "y"))