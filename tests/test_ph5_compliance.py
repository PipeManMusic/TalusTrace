import pytest
import yaml
from pathlib import Path
from core.harness import Harness
from core.wire import Wire
from core.device import Device
from infra.context import ProjectContext

def test_ph5_serialization_tuple_to_list_conversion():
    """
    Verify PH5-2.2: Ensure coordinates are serialized as Lists, not Tuples,
    to prevent !!python/tuple tags in YAML.
    """
    path_nodes = [[0.0, 0.0], [10.5, 20.0]]
    wire = Wire(
        id="W-TEST",
        source_pin_id="J1.1",
        target_pin_id="J2.1",
        path_nodes=path_nodes  # Should be accepted as List[List[float]]
    )
    harness = Harness(wires={wire.id: wire})
    context = ProjectContext(harness=harness)
    
    # Dump to string to inspect raw YAML content
    import io
    stream = io.StringIO()
    data = context.harness.model_dump(mode='json')
    yaml.safe_dump(data, stream)
    yaml_content = stream.getvalue()
    
    # Assertions
    assert "!!python/tuple" not in yaml_content, "Found Python-specific tuple tags in YAML"
    assert "[0.0, 0.0]" in yaml_content or "- 0.0" in yaml_content

def test_ph5_manufacturing_metadata():
    """
    Verify PH5-1.1: Ensure Wire and Device models contain the 
    necessary fields for industrial BOM generation.
    """
    wire = Wire(
        id="W-TP",
        source_pin_id="J1.1",
        target_pin_id="J2.1",
        type="TWISTED_PAIR", # New required field
        diameter_mm=2.5      # New required field
    )
    device = Device(
        id="J1",
        service_slack_mm=75.0 # New required field
    )
    assert wire.type == "TWISTED_PAIR"
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
    
    assert data['revision'] == 1