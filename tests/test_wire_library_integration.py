import pytest
import os
from core.library_manager import LibraryManager

def test_wire_library_loading_and_structure():
    """
    Verifies that the LibraryManager loads 'wires.yaml' and that the data 
    contains the expected DIN fields (label, family, gauge).
    """
    # 1. Setup: Calculate path to real resources
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_dir = os.path.join(base_dir, "resources", "library")
    
    # Ensure the file physically exists before testing the loader
    wires_yaml_path = os.path.join(resource_dir, "wires.yaml")
    assert os.path.exists(wires_yaml_path), f"Critical: wires.yaml not found at {wires_yaml_path}"

    # 2. Initialize LibraryManager
    # Note: This expects the updated __init__ signature that accepts resource_dir
    try:
        manager = LibraryManager(resource_dir=resource_dir)
    except TypeError:
        # Fallback for old signature (if not yet refactored) to force a meaningful failure
        manager = LibraryManager() 
        pytest.fail("LibraryManager signature mismatch. Ensure it accepts 'resource_dir' to load multiple files.")

    # 3. Verify Public API
    assert hasattr(manager, "get_wires"), "LibraryManager is missing the 'get_wires()' method."
    
    # 4. Verify Data Content
    wires = manager.get_wires()
    assert isinstance(wires, dict), "get_wires() should return a dictionary."
    assert len(wires) > 0, "Wire library is empty. YAML parsing failed or file is empty."

    # 5. Spot Check: DIN Standard Wire (FLRY-0.75)
    target_id = "FLRY-0.75"
    assert target_id in wires, f"Missing expected DIN wire '{target_id}' in loaded library."
    
    data = wires[target_id]
    
    # Check for the NEW field (Label)
    assert "label" in data, f"Wire '{target_id}' is missing the 'label' field."
    assert "0.75mm" in data["label"], "Label content does not match expected format."
    
    # Check for technical specs
    assert data["gauge"] == "0.75mm2"
    assert data["family"] == "DIN 72551 FLRY-B"

def test_wire_library_fallback_safety():
    """
    Ensures the system doesn't crash if asked for a non-existent wire.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_dir = os.path.join(base_dir, "resources", "library")
    manager = LibraryManager(resource_dir=resource_dir)
    
    wires = manager.get_wires()
    
    # Should safely return None or raise known error, depending on your strictness.
    # Standard Python dict behavior:
    assert wires.get("NON_EXISTENT_WIRE") is None