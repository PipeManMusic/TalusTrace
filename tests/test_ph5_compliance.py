import pytest
import yaml
import io
from pathlib import Path

from core.models import Harness, Wire, Device
from infra.context import ProjectContext

def test_ph5_serialization_tuple_to_list_conversion():
    """
    Verify PH5-2.2: Ensure coordinates are serialized as Lists.
    """
    path_nodes = [[0.0, 0.0], [10.5, 20.0]]
    import uuid
    wire = Wire(
        id=str(uuid.uuid4()),
        from_conn="J1.1",
        to_conn="J2.1",
        path_nodes=path_nodes 
    )
    harness = Harness(wires=[wire])
    context = ProjectContext(harness=harness)
    stream = io.StringIO()
    data = context.harness.to_dict()
    yaml.safe_dump(data, stream)
    yaml_content = stream.getvalue()
    assert "!!python/tuple" not in yaml_content
    assert "- 0.0" in yaml_content or "[0.0, 0.0]" in yaml_content

def test_ph5_manufacturing_metadata():
    """
    Verify PH5-1.1: Ensure Wire and Device models contain BOM fields.
    """
    import uuid
    wire = Wire(
        id=str(uuid.uuid4()),
        from_conn="J1.1",
        to_conn="J2.1",
        type="TWISTED_PAIR", 
        diameter_mm=2.5      
    )
    device = Device(
        id=str(uuid.uuid4()),
        service_slack_mm=75.0 
    )
    assert wire.type == "TWISTED_PAIR"
    assert wire.diameter_mm == 2.5
    assert device.service_slack_mm == 75.0
    assert wire.diameter_mm == 2.5
    assert device.service_slack_mm == 75.0

def test_ph5_optimistic_locking_logic():
    """
    Verify PH5-2.1: Test the internal revision increment and 
    validation methods in the Harness model.
    """
    harness = Harness(revision=10)
    
    # Test Increment
    harness.increment_revision()
    assert harness.revision == 11
    
    # Test Validation (Success)
    harness.validate_revision(11) # Should not raise
    
    # Test Validation (Failure - Conflict)
    with pytest.raises(RuntimeError) as exc:
        harness.validate_revision(9)
    assert "Conflict" in str(exc.value)

def test_ph5_persistence_safe_dump(tmp_path):
    """
    Verify PH5-2.2: Ensure context.save_as uses safe_dump 
    for production-grade YAML.
    """
    temp_file = tmp_path / "test_harness.yaml"
    harness = Harness(revision=1)
    context = ProjectContext(harness=harness)
    
    context.save_as(temp_file)
    
    # Verify the file can be loaded by standard safe_load
    with open(temp_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data['revision'] == 2