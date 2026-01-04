import pytest
from pydantic import ValidationError

from talus_trace.models import Harness, Meta, Connector, Pin, Wire


def sample_harness():
    return Harness(
        meta=Meta(name="Chassis", trunk_length_mm=3500),
        connectors={
            "C101": Connector(
                type="DTM-12",
                desc="Firewall",
                location_mm=0,
                branch_len_mm=0,
                pins=[Pin(id="1"), Pin(id="2")],
            ),
            "C102": Connector(
                type="MP280",
                desc="Fuel Pump",
                location_mm=3400,
                branch_len_mm=150,
                pins=[Pin(id="A"), Pin(id="B")],
            ),
        },
        wires=[
            Wire(id="W1", color="RD/WH", gauge=14, from_conn="C101.1", to_conn="C102.A"),
            Wire(id="W2", color="BK", gauge=14, from_conn="C101.2", to_conn="C102.B", length_adder_mm=50),
        ],
    )


def test_valid_harness_loads():
    h = sample_harness()
    assert h.meta.trunk_length_mm == 3500
    assert len(h.connectors) == 2
    assert len(h.wires) == 2


def test_duplicate_wire_id_rejected():
    with pytest.raises(ValidationError):
        Harness(
            meta=Meta(name="X", trunk_length_mm=1000),
            connectors={"C1": Connector(type="DTM", location_mm=0)},
            wires=[
                Wire(id="W1", color="RD", gauge=18, from_conn="C1.1", to_conn="C1.1"),
                Wire(id="W1", color="BK", gauge=18, from_conn="C1.1", to_conn="C1.1"),
            ],
        )


def test_unknown_connector_rejected():
    with pytest.raises(ValidationError):
        Harness(
            meta=Meta(name="X", trunk_length_mm=1000),
            connectors={"C1": Connector(type="DTM", location_mm=0)},
            wires=[Wire(id="W1", color="RD", gauge=18, from_conn="C2.1", to_conn="C1.1")],
        )


def test_unknown_pin_rejected_when_declared():
    with pytest.raises(ValidationError):
        Harness(
            meta=Meta(name="X", trunk_length_mm=1000),
            connectors={"C1": Connector(type="DTM", location_mm=0, pins=[Pin(id="1")])},
            wires=[Wire(id="W1", color="RD", gauge=18, from_conn="C1.2", to_conn="C1.1")],
        )


def test_connector_location_within_trunk():
    with pytest.raises(ValidationError):
        Harness(
            meta=Meta(name="X", trunk_length_mm=1000),
            connectors={"C1": Connector(type="DTM", location_mm=1500)},
            wires=[],
        )


def test_endpoint_format_validation():
    with pytest.raises(ValidationError):
        Wire(id="W1", color="RD", gauge=18, from_conn="C1", to_conn="C1.1")
