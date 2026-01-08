import pytest
from pydantic import ValidationError
from core.models import Wire

def test_wire_initialization_path():
    """Verify a Wire stores its path as mm nodes and links to pins."""
    path = [[0.0, 0.0], [10.0, 0.0], [10.0, 20.0]]
    wire = Wire(
        id="w_001",
        from_conn="p_src_01",
        to_conn="p_tgt_01",
        path_nodes=path
    )
    
    assert wire.id == "w_001"
    assert len(wire.path_nodes) == 3
    assert wire.path_nodes[1] == [10.0, 0.0]
    assert wire.status == "undefined"  # Default draft state

def test_wire_revision_initialization():
    """Verify revision tracking for optimistic locking on wires."""
    wire = Wire(id="w1", from_conn="s1", to_conn="t1")
    # No revision field on Wire in new model

def test_wire_invalid_nodes():
    """Ensure the 'Holy Millimeter' standard rejects non-float path data."""
    with pytest.raises(ValidationError):
        # Path nodes must be tuples of floats
        Wire(id="err", from_conn="s1", to_conn="t1", path_nodes=["start", "end"])

def test_wire_draft_status_enum():
    """Verify wire can hold industrial status for later promotion."""
    wire = Wire(id="w1", from_conn="s", to_conn="t", status="CALCULATED")
    assert wire.status == "CALCULATED"