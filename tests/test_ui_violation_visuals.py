import pytest
from PySide6.QtGui import QColor
from ui.items import BundleItem
from ui.coordinates import CoordinateTransformer

def test_ph4_3_2_visual_violation_highlight(qtbot):
    """
    Ensures UI items reflect 'ERROR' state (Red) when bend radius is violated.
    Updated to use correct 'wire_diameters' argument.
    """
    transformer = CoordinateTransformer()
    transformer.pixels_per_inch = 20.0
    # Create a path with a sharp 90-degree turn (Violation)
    # Lengths are 5mm, requiring a much larger radius for 5mm wire
    sharp_path = [(0, 0), (5, 0), (5, 5)]
    wire_diameter = 5.0 
    
    # Fix: Argument name aligned with items.py implementation
    item = BundleItem(path_nodes=sharp_path, wire_diameters=[wire_diameter], transformer=transformer)
    
    # Trigger the compliance check logic
    item.update_compliance_visuals()
    
    # Aligned with Canvas Spec: Violations must render in RED
    assert item.pen().color() == QColor("red")