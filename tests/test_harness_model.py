import pytest
from core.harness import Harness
from core.device import Device
from core.wire import Wire
from core.twisted_pair import TwistedPair

def test_harness_schema_and_serialization():
    # Create a harness with devices, wires, and twisted pairs
    harness = Harness(
        revision=3,
        meta={"project": "Test"},
        devices=[Device(id="dev1"), Device(id="dev2")],
        wires=[Wire(id="w1", from_conn="dev1.P1", to_conn="dev2.P2")],
        twisted_pairs=[TwistedPair(id="tp1", node_a=[0.0,0.0], node_b=[1.0,1.0])]
    )
    # Validate schema
    assert harness.revision == 3
    assert harness.devices[0].id == "dev1"
    assert harness.wires[0].id == "w1"
    assert harness.twisted_pairs[0].id == "tp1"
    # Test serialization
    data = harness.model_dump()
    assert data["revision"] == 3
    assert data["devices"][1]["id"] == "dev2"
    # Test deserialization
    harness2 = Harness.model_validate(data)
    assert harness2 == harness
    # Test revision increment
    harness.increment_revision()
    assert harness.revision == 4
    # Test revision validation
    harness.validate_revision(4)
    with pytest.raises(RuntimeError):
        harness.validate_revision(2)
