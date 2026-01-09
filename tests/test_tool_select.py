import pytest
from PySide6.QtCore import QPointF, QRectF
from tools.select_tool import SelectTool
from core.models import Harness, Device

def test_marquee_selection_logic():
    """PH5-INTER.1: Validate Enclosing vs Crossing selection logic."""
    harness = Harness()
    # Device at (10, 10) size 20x20 -> Bounds (0, 0) to (20, 20)
    d1 = Device(id="D1", x=10, y=10)
    harness.add_device(d1)
    
    tool = SelectTool()
    tool._get_harness = lambda: harness # Mock harness access
    
    # 1. Enclosing Selection (Left-to-Right drag)
    # Box completely surrounds D1
    enclosing_rect = QRectF(0, 0, 50, 50)  # (0,0) to (50,50) fully encloses (10,10)-(30,30)
    hits = tool._calculate_marquee_hits(enclosing_rect, crossing=False)
    assert d1 in hits

    # 2. Partial Selection (Left-to-Right drag)
    # Box clips the corner of D1 -> Should NOT select (Enclosing mode)
    partial_rect = QRectF(20, 20, 20, 20)  # (20,20)-(40,40) only clips lower-right corner
    hits = tool._calculate_marquee_hits(partial_rect, crossing=False)
    assert d1 not in hits

    # 3. Crossing Selection (Right-to-Left drag logic usually triggers this)
    # Box clips the corner of D1 -> Should select (Crossing mode)
    hits = tool._calculate_marquee_hits(partial_rect, crossing=True)
    assert d1 in hits