import pytest
import json
from pathlib import Path
# Assuming utility resides in ui/coordinates.py or ui/utils.py
from ui.coordinates import CoordinateTransformer

def test_mm_to_pixel_transformation(tmp_path):
    """
    Validates PH1-4.2: UI: Coordinate Transformation Math.
    Ensures mm values are scaled to pixels based on theme_tokens logic.
    """
    # 1. Setup mock theme tokens with a defined physical scale
    # Example: 1mm = 10 pixels
    theme_file = tmp_path / "theme_tokens.json"
    mock_tokens = {
        "dimensions": {
            "physical_scale": 10.0,  # pixels per mm
            "grid_size_mm": 2.0      # 2mm grid
        }
    }
    theme_file.write_text(json.dumps(mock_tokens))

    # 2. Initialize transformer
    transformer = CoordinateTransformer(theme_path=theme_file)

    # 3. Test basic scaling (10mm should be 100 pixels)
    assert transformer.mm_to_px(10.0) == 100.0
    assert transformer.mm_to_px(0.5) == 5.0

    # 4. Test inverse scaling (pixels to mm for status bar/readouts)
    assert transformer.px_to_mm(100.0) == 10.0

def test_grid_snapping_mm_logic(tmp_path):
    """
    Ensures that coordinate transformations respect the grid-snapping
    requirements defined in the Intent spec (Section 3).
    """
    theme_file = tmp_path / "theme_tokens.json"
    mock_tokens = {
        "dimensions": {
            "physical_scale": 5.0, # 1mm = 5px
            "grid_size_mm": 4.0    # 4mm grid = 20px snap (Matches Roadmap #10, #23)
        }
    }
    theme_file.write_text(json.dumps(mock_tokens))
    
    transformer = CoordinateTransformer(theme_path=theme_file)
    
    # Input 4.1mm should snap to the 4.0mm grid line
    # 4.1mm -> 20.5px -> Snap to 20px
    raw_px = transformer.mm_to_px(4.1)
    snapped_px = transformer.snap_to_grid(raw_px)
    
    assert snapped_px == 20.0
    assert transformer.px_to_mm(snapped_px) == 4.0

def test_zero_scale_safety():
    """Ensures the transformer handles missing or zero scale gracefully."""
    # Should fallback to 1:1 or a safe default rather than Dividing by Zero
    transformer = CoordinateTransformer(theme_path=Path("non_existent.json"))
    assert transformer.mm_to_px(10.0) == 10.0