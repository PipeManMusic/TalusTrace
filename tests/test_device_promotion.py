import pytest
from core.device import Device

def test_device_promotion_source_id():
    # Device with promotion_source_id
    import uuid
    ancestor_id = str(uuid.uuid4())
    dev_id = str(uuid.uuid4())
    dev = Device(id=dev_id, promotion_source_id=ancestor_id)
    assert dev.promotion_source_id == ancestor_id

def test_device_promotion_source_id_default():
    # Device without promotion_source_id
    import uuid
    dev = Device(id=str(uuid.uuid4()))
    assert dev.promotion_source_id is None

def test_device_promotion_serialization():
    import uuid
    ancestor_id = str(uuid.uuid4())
    dev_id = str(uuid.uuid4())
    dev = Device(id=dev_id, promotion_source_id=ancestor_id)
    data = dev.to_dict()
    assert data["promotion_source_id"] == ancestor_id
    # Deserialize
    dev2 = Device.from_dict(data)
    assert dev2.promotion_source_id == ancestor_id
