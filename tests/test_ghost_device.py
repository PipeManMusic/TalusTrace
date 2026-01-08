import pytest
from core.device import Device

def test_ghost_device_flag():
    # Device with is_ghost True
    ghost = Device(id="ghost1", is_ghost=True)
    assert ghost.is_ghost is True

def test_ghost_device_default():
    # Device with is_ghost default (should be False)
    dev = Device(id="dev1")
    assert dev.is_ghost is False

def test_ghost_device_serialization():
    ghost = Device(id="ghost2", is_ghost=True)
    data = ghost.model_dump()
    assert data["is_ghost"] is True
    # Deserialize
    ghost2 = Device.model_validate(data)
    assert ghost2.is_ghost is True
