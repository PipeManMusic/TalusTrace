import pytest
from core.geometry import snap_to_grid_mm

def test_mm_grid_snapping_logic():
    """
    Validates PH2-1.1: Core: Orthogonal Grid Snapping Logic.
    Ensures mm values round to the nearest 2px (at 10px/mm scale = 20px snap).
    """
    # Assuming theme_tokens.json: physical_scale=10.0, grid_size_px=20
    # 20px / 10px/mm = 2mm grid step
    grid_step_mm = 2.0
    
    # Test snapping up
    assert snap_to_grid_mm(2.1, grid_step_mm) == 2.0
    assert snap_to_grid_mm(3.9, grid_step_mm) == 4.0
    
    # Test exact alignment
    assert snap_to_grid_mm(6.0, grid_step_mm) == 6.0
    
    # Test negative coordinates
    assert snap_to_grid_mm(-1.9, grid_step_mm) == -2.0