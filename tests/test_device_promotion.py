import pytest
from core.device import Device

def test_device_promotion_source_id():
    # Device with promotion_source_id
    dev = Device(id="dev2", promotion_source_id="dev1")
    assert dev.promotion_source_id == "dev1"

def test_device_promotion_source_id_default():
    # Device without promotion_source_id
    dev = Device(id="dev3")
    assert dev.promotion_source_id is None

def test_device_promotion_serialization():
    dev = Device(id="dev4", promotion_source_id="ancestor1")
    data = dev.model_dump()
    assert data["promotion_source_id"] == "ancestor1"
    # Deserialize
    dev2 = Device.model_validate(data)
    assert dev2.promotion_source_id == "ancestor1"
