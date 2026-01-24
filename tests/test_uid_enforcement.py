import uuid
import pytest
from core.device import Device
from core.pin import Pin
from core.wire import Wire

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False

def test_device_id_is_uuid():
    d = Device()
    assert is_valid_uuid(d.id), f"Device id is not a valid UUID: {d.id}"

def test_pin_id_is_uuid():
    p = Pin()
    assert is_valid_uuid(p.id), f"Pin id is not a valid UUID: {p.id}"

def test_wire_id_is_uuid():
    w = Wire(from_conn="A", to_conn="B")
    assert is_valid_uuid(w.id), f"Wire id is not a valid UUID: {w.id}"
