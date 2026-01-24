import pytest
from core.device import Device

def test_ghost_device_flag():
    # Device with is_ghost True
    import uuid
    ghost = Device(id=str(uuid.uuid4()), is_ghost=True)
    assert ghost.is_ghost is True

def test_ghost_device_default():
    # Device with is_ghost default (should be False)
    import uuid
    dev = Device(id=str(uuid.uuid4()))
    assert dev.is_ghost is False

def test_ghost_device_serialization():
    import uuid
    ghost = Device(id=str(uuid.uuid4()), is_ghost=True)
    data = ghost.to_dict()
    assert data["is_ghost"] is True
    # Deserialize
    ghost2 = Device.from_dict(data)
    assert ghost2.is_ghost is True
