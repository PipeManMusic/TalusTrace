import pytest
import yaml
import os
from pathlib import Path

# CONSTANTS
RESOURCE_ROOT = Path("resources")
CACHE_ROOT = Path(".cache")

def test_directory_structure_exists():
    """
    Validates Phase 7c: Granular Database Architecture.
    Ensures user-editable resources and system caches are separated.
    """
    required_dirs = [
        RESOURCE_ROOT / "config",
        RESOURCE_ROOT / "library",
        RESOURCE_ROOT / "rules",
        CACHE_ROOT / "render",
        CACHE_ROOT / "routing"
    ]
    
    for d in required_dirs:
        assert d.exists(), f"Critical Architecture Failure: Missing directory {d}"
        assert d.is_dir(), f"Path is not a directory: {d}"

def test_pro_shortcuts_loaded():
    """
    Validates the 'Pro' Workflow defaults (G for Move, Space for Rotate).
    """
    config_path = RESOURCE_ROOT / "config/actions.yaml"
    assert config_path.exists(), "Actions registry missing."
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Flatten list to dict for checking
    actions = {cmd['id']: cmd for cmd in data['commands']}
    
    # 1. Check 'Grab' (Blender Style)
    assert "edit.move" in actions
    assert actions["edit.move"]["default_key"] == "G"
    
    # 2. Check 'Rotate' (Spacebar)
    assert "edit.rotate_cw" in actions
    assert actions["edit.rotate_cw"]["default_key"] == "Space"

def test_wire_physics_data():
    """
    Validates that the Engineering Engine has physical data to load.
    """
    lib_path = RESOURCE_ROOT / "library/wires.yaml"
    assert lib_path.exists()
    
    with open(lib_path, 'r') as f:
        data = yaml.safe_load(f)
        
    # Check TXL-18 Spec
    wire = data["wires"].get("TXL-18")
    assert wire is not None
    assert wire["od_mm"] == 2.18
    assert wire["weight_g_m"] == 9.6

def test_cache_is_ignored():
    """
    Validates that the binary cache is excluded from Git to prevent bloat.
    """
    gitignore = Path(".gitignore")
    assert gitignore.exists()
    
    with open(gitignore, 'r') as f:
        content = f.read()
        
    assert ".cache/" in content, "Security Risk: System cache is not git-ignored."

def test_ui_layout_fallback():
    """
    Validates that the UI Layout schema is present.
    """
    layout_path = RESOURCE_ROOT / "config/ui_layout.yaml"
    assert layout_path.exists()
    
    with open(layout_path, 'r') as f:
        layout = yaml.safe_load(f)
        
    assert "toolbar" in layout
    assert "context_menu" in layout
    # Ensure Save is the first toolbar item
    assert layout["toolbar"]["items"][0]["command"] == "file.save"