import pytest
from pydantic import ValidationError
from talustrace.backend.models import Harness, Device, Wire, Side

def test_device_auto_pins():
    """Verify 'pins: 4' automatically generates 4 Pin objects."""
    d = Device(id="D1", label="Test", pins=4)
    assert len(d.pins) == 4
    assert d.pins[0].id == "1"
    assert d.pins[3].id == "4"
    assert d.pins[0].side == Side.LEFT

def test_wire_endpoint_validation():
    """Verify wires catch bad endpoint formats."""
    # Valid
    w = Wire(id="W1", from_conn="D1.1", to_conn="D2.1", color="RD")
    assert w.from_conn == "D1.1"

    # Invalid (Missing dot)
    with pytest.raises(ValidationError):
        Wire(id="W2", from_conn="D1", to_conn="D2", color="BK")

def test_full_harness_load():
    """Verify a complete harness structure."""
    data = {
        "meta": {"name": "Engine Harness"},
        "devices": [
            {"id": "ECU", "label": "MS3Pro", "pins": 35},
            {"id": "J1", "label": "Firewall", "pins": [{"id": "A", "side": "right"}]}
        ],
        "wires": [
            {"id": "101", "from": "ECU.1", "to": "J1.A", "color": "PK", "stripe": "BK"}
        ]
    }
    h = Harness(**data)
    assert len(h.devices) == 2
    assert h.wires[0].stripe == "BK"
    assert h.devices[0].pins[34].id == "35"