import pytest
import json
from pathlib import Path
# Assuming utility resides in ui/coordinates.py or ui/utils.py
from ui.coordinates import CoordinateTransformer

def test_mm_to_pixel_transformation(tmp_path):
    """
    Validates PH1-4.2: UI: Coordinate Transformation Math.
    Matches mandated formula: (mm / 25.4) * PPI.
    """
    theme_file = tmp_path / "theme_tokens.json"
    # Setting scale to 25.4 means 1mm = 1px for easy math validation
    mock_tokens = {
        "dimensions": {
            "physical_scale": 254.0,  # 10x scale: 100px = 10mm
            "grid_size_mm": 2.0
        }
    }
    theme_file.write_text(json.dumps(mock_tokens))

    transformer = CoordinateTransformer(theme_path=str(theme_file))

    assert transformer.mm_to_px(0.5) == pytest.approx(5.0)
    assert transformer.px_to_mm(1.0) == pytest.approx(0.1)

    # 4. Test inverse scaling (pixels to mm for status bar/readouts)
    assert transformer.px_to_mm(100.0) == pytest.approx(10.0)

def test_grid_snapping_mm_logic(tmp_path):
    """
    Ensures snapping respects the grid_size_mm regardless of PPI.
    """
    theme_file = tmp_path / "theme_tokens.json"
    mock_tokens = {
        "dimensions": {
            "physical_scale": 50.8, # 1mm = 2px
            "grid_size_mm": 2.0    # 2mm grid = 4px snap
        }
    }
    theme_file.write_text(json.dumps(mock_tokens))
    
    transformer = CoordinateTransformer(theme_path=theme_file)
    
    # 2.1mm -> ~4.2px -> Snaps to 4.0px (which is 2.0mm)
    raw_px = transformer.mm_to_px(2.1)
    snapped_px = transformer.snap_to_grid(raw_px)
    
    assert snapped_px == pytest.approx(4.0)
    assert transformer.px_to_mm(snapped_px) == pytest.approx(2.0)

def test_zero_scale_safety():
    """Ensures the transformer handles missing or zero scale gracefully."""
    # Should fallback to 1:1 or a safe default rather than Dividing by Zero
    transformer = CoordinateTransformer(theme_path=Path("non_existent.json"))
    expected = (10.0 / 25.4) * 20.0
    assert transformer.mm_to_px(10.0) == pytest.approx(expected)