import pytest
from PySide6.QtGui import QColor
from ui.items import BundleItem
from ui.coordinates import CoordinateTransformer, THEME_FALLBACK

def test_ph4_3_2_visual_violation_highlight(qtbot):
    """
    Ensures UI items reflect 'ERROR' state (Red) when bend radius is violated.
    """
    # Create a path with a sharp 90-degree turn (Violation)
    # Lengths are 5mm, requiring a much larger radius for 5mm wire
    sharp_path = [(0, 0), (5, 0), (5, 5)]
    wire_diameter = 5.0 
    
    # FIX: Removed 'transformer' argument. 
    # BundleItem now uses ui.coordinates.THEME_FALLBACK internally or global config.
    item = BundleItem(path_nodes=sharp_path, wire_diameters=[wire_diameter])
    
    # Manually inject a violation color into the fallback for this test context if needed,
    # or rely on the fact that BundleItem checks logic internally.
    # For this test to pass with the current implementation, we assume BundleItem
    # switches to THEME_FALLBACK["bundle_violation"] which is #FF0000.
    
    # Trigger the compliance check logic (if method exists) or rely on init
    if hasattr(item, 'update_compliance_visuals'):
        item.update_compliance_visuals()
    
    # Verify Color is Red (#FF0000)
    expected_color = QColor(THEME_FALLBACK["bundle_violation"])
    assert item.pen().color() == expected_color