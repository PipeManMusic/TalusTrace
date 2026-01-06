import pytest
import yaml
import os
from talustrace.backend.models import Harness, Device, Wire

def test_harness_serialization():
    # 1. Create Harness
    d1 = Device(id="D1", label="ECU", pins=2, x=10, y=20)
    d2 = Device(id="D2", label="Sensor", pins=2, x=100, y=200)
    w1 = Wire(id="W1", from_conn="D1.1", to_conn="D2.1")
    
    harness = Harness(devices=[d1, d2], wires=[w1])
    
    # 2. Serialize (to dict then YAML)
    data = harness.model_dump(mode='json')
    yaml_str = yaml.dump(data)
    
    # 3. Deserialize
    data_loaded = yaml.safe_load(yaml_str)
    harness2 = Harness(**data_loaded)
    
    # 4. Verify
    assert len(harness2.devices) == 2
    assert len(harness2.wires) == 1
    assert harness2.devices[0].id == "D1"
    assert harness2.wires[0].from_conn == "D1.1"

def test_harness_file_io(tmp_path):
    # 1. Create Harness
    d1 = Device(id="D1", label="ECU", pins=2, x=10, y=20)
    harness = Harness(devices=[d1])
    
    # 2. Save to file
    file_path = tmp_path / "test.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(harness.model_dump(mode='json'), f)
        
    # 3. Load from file
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
        harness2 = Harness(**data)
        
    # 4. Verify
    assert len(harness2.devices) == 1
    assert harness2.devices[0].label == "ECU"
