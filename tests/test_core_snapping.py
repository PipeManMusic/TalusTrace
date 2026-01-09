import pytest
from PySide6.QtCore import QPointF
from core.spatial import SpatialManager # Assuming logic lives here or tool base

def test_dynamic_snapping_config():
    """PH5-INTER.3: Grid size should be configurable."""
    # Setup a mock tool/manager that handles snapping
    manager = SpatialManager()
    
    # Default 25mm
    manager.grid_size = 25.0
    point = (26.0, 52.0)
    snapped = manager.snap(point)
    assert snapped == (25.0, 50.0)

    # Change to 10mm
    manager.grid_size = 10.0
    snapped = manager.snap(point)
    assert snapped == (30.0, 50.0) # Closest 10 is 30

    # Toggle Off
    manager.snap_enabled = False
    snapped = manager.snap(point)
    assert snapped == (26.0, 52.0)