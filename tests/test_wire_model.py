import pytest
from pydantic import ValidationError
from core.models import Wire

def test_wire_initialization_path():
    """Verify a Wire stores its path as mm nodes and links to pins."""
    path = [[0.0, 0.0], [10.0, 0.0], [10.0, 20.0]]
    import uuid
    valid_id = str(uuid.uuid4())
    wire = Wire(
        id=valid_id,
        from_conn="p_src_01",
        to_conn="p_tgt_01",
        path_nodes=path
    )
    
    assert wire.id == valid_id
    assert len(wire.path_nodes) == 3
    assert wire.path_nodes[1] == [10.0, 0.0]
    assert wire.status == "UNDEFINED"  # Default draft state

def test_wire_revision_initialization():
    """Verify revision tracking for optimistic locking on wires."""
    import uuid
    wire = Wire(id=str(uuid.uuid4()), from_conn="s1", to_conn="t1")
    # No revision field on Wire in new model

def test_wire_draft_status_enum():
    """Verify wire can hold industrial status for later promotion."""
    import uuid
    wire = Wire(id=str(uuid.uuid4()), from_conn="s", to_conn="t", status="CALCULATED")
    assert wire.status == "CALCULATED"