import pytest
import json
from pathlib import Path
from PySide6.QtGui import QColor
# Assuming the utility is placed in ui/utils.py or ui/theme.py
from ui.coordinates import CoordinateTransformer

def test_theme_token_resolution(tmp_path):
    """
    Validates PH1-4.1: UI: Theme Token Loader Utility.
    Ensures semantic keys (e.g., 'wire_default') resolve to correct QColor objects.
    """
    # 1. Setup a mock theme_tokens.json based on project specs
    theme_file = tmp_path / "theme_tokens.json"
    mock_tokens = {
        "colors": {
            "wire_default": "#000000",
            "wire_signal_hi": "#FF0000",
            "grid_line": "#E0E0E0"
        },
        "dimensions": {
            "wire_width_px": 3,
            "control_node_radius": 10
        }
    }
    theme_file.write_text(json.dumps(mock_tokens))

    # 2. Initialize loader with the mock file
    transformer = CoordinateTransformer(theme_path=str(theme_file))

    # 3. Test Color Resolution (Semantic Key -> QColor)
    wire_color = transformer.get_color("wire_default")
    assert isinstance(wire_color, QColor)
    assert wire_color.name().upper() == "#000000"

    # 4. Test Dimension Resolution (Semantic Key -> Int/Float)
    assert transformer.get_dimension("wire_width_px") == 3
    assert transformer.get_dimension("control_node_radius") == 10

def test_theme_loader_fallback():
    """Ensures the loader provides a safe fallback for missing tokens."""
    transformer = CoordinateTransformer() # Uses default project theme_tokens.json
    # Resolving a non-existent key should return magenta fallback
    fallback_color = transformer.get_color("non_existent_key")
    assert isinstance(fallback_color, QColor)
    assert fallback_color.name().upper() == "#FF00FF"

def test_theme_file_location():
    """Enforces that the theme_tokens.json exists in the mandated specs folder."""
    spec_path = Path("resources/theme_tokens.json")
    assert spec_path.exists(), "Architecture Violation: theme_tokens.json missing from resources/"