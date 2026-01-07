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
    # 1. Setup Model with physical metadata (100mm x 50mm)
    dev_model = Device(
        id="dev_001", 
        label="ECU", 
        meta={"width_mm": 100, "height_mm": 50}
    )
    
    # 2. Initialize Transformer (1mm = 10px)
    # This aligns with PH1-4.2 Coordinate Transformation Math
    transformer = CoordinateTransformer(scale=10.0)
    
    # 3. Create Visual Item
    item = DeviceItem(dev_model, transformer=transformer)
    
    # 4. Assert Bounding Rect matches (1000px x 500px)
    rect = item.boundingRect()
    assert rect.width() == 1000.0
    assert rect.height() == 500.0

def test_ghost_device_visual_state():
    """
    Validates PH1-4.4: Logic for red dashed outline if is_ghost is True.
    Supports Section 4 of Project Intent (Ghosting).
    """
    dev_model = Device(id="ghost_001", label="Missing Library Asset")
    
    # Initialize as a ghost
    item = DeviceItem(dev_model, is_ghost=True)
    
    # Get the pen used for the main rectangle outline
    # Implementation should use this to signify 'Logical Skeleton' only
    pen = item.get_outline_pen() 
    
    assert pen.color() == QColor("red")
    assert pen.style() == Qt.PenStyle.DashLine

def test_standard_device_visual_state():
    """Ensures non-ghost devices use the standard industrial theme."""
    dev_model = Device(id="std_001", label="Valid Connector")
    item = DeviceItem(dev_model, is_ghost=False)
    
    pen = item.get_outline_pen()
    
    # Matches Spec: 3px solid lines for standard view
    assert pen.style() == Qt.PenStyle.SolidLine
    assert pen.width() == 3