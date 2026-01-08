import pytest
from pydantic import ValidationError
from core.models import Pin

def test_pin_initialization_valid():
    """Verify a Pin can be created with valid mm coordinates and defaults."""
    pin = Pin(
        id="pin_001",
        head=[10.5, 20.0],
        tail=[10.5, 15.0],
        name="J1-A"
    )
    assert pin.id == "pin_001"
    assert pin.head == [10.5, 20.0]
    assert pin.is_ghost is False  # Check default
    assert pin.revision == 0

def test_pin_exit_vector_calculation():
    """Verify the vector math correctly identifies the orthogonal direction."""
    # Vector pointing strictly Up (positive Y)
    pin_up = Pin(id="p1", head=[0, 10], tail=[0, 5])
    assert pin_up.exit_vector == [0, 5]

    # Vector pointing strictly Right (positive X)
    pin_right = Pin(id="p2", head=[10, 0], tail=[5, 0])
    assert pin_right.exit_vector == [5, 0]

def test_pin_type_enforcement():
    """Ensure the 'Holy Millimeter' standard rejects non-float data."""
    with pytest.raises(ValidationError):
        # Attempting to pass strings instead of float lists
        Pin(id="err", head=["top", "left"], tail=[0, 0])

def test_pin_ghost_status():
    """Verify pins can be explicitly marked as ghosts for 'Draft-First' design."""
    pin = Pin(id="ghost_1", head=[0, 0], tail=[0, 0], is_ghost=True)
    assert pin.is_ghost is True