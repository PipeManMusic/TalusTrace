import pytest
import yaml
from pathlib import Path
from ui.theme import ThemeManager
from ui.layout_manager import LayoutManager
from resources.defaults import DEFAULT_THEME, DEFAULT_LAYOUT

def test_theme_manager_fallback(tmp_path):
    """
    PH5-CLN.2: Verify ThemeManager falls back to hardcoded defaults on load failure.
    """
    # Point to a non-existent file
    manager = ThemeManager(user_path=str(tmp_path / "missing_theme.yaml"))
    
    # Force a load attempt
    manager._load_user_theme()
    
    # Should match hardcoded factory background
    assert manager.get_color("canvas_bg") == DEFAULT_THEME["canvas_bg"]

def test_layout_manager_fallback():
    """
    PH5-CLN.2: Verify LayoutManager falls back to hardcoded defaults on load failure.
    """
    # Provide a path to a non-existent file
    manager = LayoutManager(layout_path="invalid/path.yaml")
    
    # Should have loaded the default context menu keys
    assert "device" in manager.layout_cfg["context_menu"]
    assert manager.layout_cfg["context_menu"]["device"][0]["command"] == "edit.move"