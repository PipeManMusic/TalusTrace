import pytest
from ui.layout_manager import LayoutManager

def test_layout_manager_fallback():
    """
    PH5-CLN.2: Verify LayoutManager falls back to hardcoded defaults on load failure.
    """
    # Provide a path to a non-existent file
    # FIX: Use 'config_path' instead of 'layout_path'
    manager = LayoutManager(config_path="invalid/path.yaml")
    
    # Should handle gracefully and have empty config
    assert manager.config == {}