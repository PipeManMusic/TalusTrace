import pytest
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

# Assuming standard architectural locations
from core.models import Device
from ui.items import DeviceItem
from ui.coordinates import CoordinateTransformer

def test_device_rect_scaling(qtbot):
    """
    Validates PH1-4.4: UI: Implement Generic DeviceItem Visuals.
    Ensures the bounding rect matches core mm scaled by the transformer.
    """
    dev_model = Device(
        id="dev_001", 
        meta={"width_mm": 25.4, "height_mm": 25.4}
    )
    
    # 1mm = 1px for verification
    transformer = CoordinateTransformer()
    transformer.pixels_per_inch = 25.4
    item = DeviceItem(dev_model, transformer=transformer)
    
    rect = item.rect() # DeviceItem inherits from QGraphicsRectItem
    assert rect.width() == 25.4
    assert rect.height() == 25.4

def test_ghost_device_visual_state():
    """
    Validates PH1-4.4: Logic for red dashed outline if is_ghost is True.
    Supports Section 4 of Project Intent (Ghosting).
    """
    dev_model = Device(id="ghost_001")
    transformer = CoordinateTransformer()
    transformer.pixels_per_inch = 25.4
    
    item = DeviceItem(dev_model, transformer=transformer, is_ghost=True)
    pen = item.get_outline_pen() 
    
    assert pen.style() == Qt.PenStyle.DashLine

def test_standard_device_visual_state():
    """Ensures non-ghost devices use the standard industrial theme."""
    dev_model = Device(id="std_001")
    transformer = CoordinateTransformer()
    transformer.pixels_per_inch = 25.4
    item = DeviceItem(dev_model, transformer=transformer, is_ghost=False)
    pen = item.get_outline_pen()
    assert pen.style() == Qt.PenStyle.SolidLine
    assert pen.width() == 3