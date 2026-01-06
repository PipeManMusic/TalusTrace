import pytest
from typing import Optional

# This import will fail until you implement the model, as intended for TDD
from talustrace.backend.models import TwistedPair

def test_atomic_structure_instantiation():
    pair = TwistedPair(
        id="tp-001",
        node_a=(0.0, 0.0),
        node_b=(100.0, 50.0),
        rotation_a=0,
        rotation_b=0,
        wire_id_1=None,
        wire_id_2=None
    )
    assert pair.id == "tp-001"
    assert pair.node_a == (0.0, 0.0)
    assert pair.node_b == (100.0, 50.0)
    assert pair.rotation_a == 0
    assert pair.rotation_b == 0
    assert pair.wire_id_1 is None
    assert pair.wire_id_2 is None

def test_validation_of_coordinates():
    # Valid coordinates
    TwistedPair(id="tp-002", node_a=(1.0, 2.0), node_b=(3.0, 4.0))
    # Invalid coordinates (should fail)
    with pytest.raises(Exception):
        TwistedPair(id="tp-003", node_a=(1.0,), node_b=(3.0, 4.0))
    with pytest.raises(Exception):
        TwistedPair(id="tp-004", node_a="not-a-tuple", node_b=(3.0, 4.0))

def test_migration_from_legacy_bundle():
    legacy_bundle = {
        "from_node": "uuid1",
        "to_node": "uuid2",
        "elbow": [100.0, 50.0]
    }
    # Simulate migration logic (to be implemented later)
    # For now, just manually map the data
    pair = TwistedPair(
        id="tp-legacy",
        node_a=(0.0, 0.0),  # would be looked up from uuid1
        node_b=tuple(legacy_bundle["elbow"]),
        rotation_a=0,
        rotation_b=0,
        wire_id_1=None,
        wire_id_2=None
    )
    assert pair.node_b == (100.0, 50.0)
    assert pair.id == "tp-legacy"
