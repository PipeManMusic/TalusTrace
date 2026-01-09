import pytest
import yaml
from ui.theme import ThemeManager

def test_theme_user_persistence(tmp_path):
    """PH5-EDIT.1: User theme overrides should save to disk."""
    user_theme_path = tmp_path / "user_theme.yaml"
    manager = ThemeManager(user_path=str(user_theme_path))
    
    # Verify Default
    assert manager.get_color("canvas_bg") != "#FF0000"
    
    # Set Custom Color
    manager.set_color_override("canvas_bg", "#FF0000")
    manager.save_user_theme()
    
    # Check File
    assert user_theme_path.exists()
    data = yaml.safe_load(user_theme_path.read_text())
    assert data["colors"]["canvas_bg"] == "#FF0000"