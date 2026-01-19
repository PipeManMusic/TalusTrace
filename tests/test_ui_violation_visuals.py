import pytest
from unittest.mock import MagicMock
from PySide6.QtGui import QColor
from ui.items import WireItem
from ui.coordinates import THEME_FALLBACK

def test_ph4_3_2_visual_violation_highlight(qtbot):
    """
    Ensures UI items reflect 'ERROR' state (Red) when bend radius is violated.
    """
    # 1. Setup Dummy Model
    sharp_path = [(0, 0), (5, 0), (5, 5)]
    wire_diameter = 5.0 
    item = WireItem(wire_model=type('Wire', (), {'path_nodes': sharp_path, 'gauge': wire_diameter, 'color': '#808080'})())
    
    # 2. Mock ThemeManager to guarantee 'bundle_violation' is Red (#FF0000)
    # This prevents external JSON files from breaking this test.
    item.theme = MagicMock()
    def get_color_mock(token):
        if token == "bundle_violation": return QColor("#FF0000")
        if token == "bundle_standard": return QColor("#333333")
        return QColor("#000000")
    item.theme.get_color.side_effect = get_color_mock
    
    # 3. Manually trigger violation visual
    item.update_compliance_visuals(is_violation=True)
    
    # 4. Verify Color is Red (#FF0000)
    assert item.pen().color() == QColor("#FF0000")
    
    # 5. Verify return to normal
    # We expect it to use model color (#808080) if defined, or theme standard
    item.update_compliance_visuals(is_violation=False)
    assert item.pen().color() == QColor('#808080')