import pytest
from core.harness import Harness
from core.device import Device
from core.wire import Wire

def test_harness_schema_and_serialization():
    # Create a harness with devices, wires, and twisted pairs
    import uuid
    dev1_id = str(uuid.uuid4())
    dev2_id = str(uuid.uuid4())
    wire_id = str(uuid.uuid4())
    harness = Harness(
        revision=3,
        meta={"project": "Test"},
        devices=[Device(id=dev1_id), Device(id=dev2_id)],
        wires=[Wire(id=wire_id, from_conn=f"{dev1_id}.P1", to_conn=f"{dev2_id}.P2")],
    )
    # Validate schema
    assert harness.revision == 3
    assert harness.devices[0].id == dev1_id
    assert harness.wires[0].id == wire_id
    # Test serialization
    data = harness.to_dict()
    assert data["revision"] == 3
    assert data["devices"][1]["id"] == dev2_id
    # Test deserialization
    harness2 = Harness.from_dict(data)
    assert harness2 == harness
    # Test revision increment
    harness.increment_revision()
    assert harness.revision == 4
    # Test revision validation
    harness.validate_revision()
