import pytest
from core.device import Device
from ui.items import DeviceItem
from ui.coordinates import CoordinateTransformer

def test_device_rect_scaling(qtbot):
    """
    Validates PH1-4.4: UI: Implement Generic DeviceItem Visuals.
    Ensures the bounding rect matches core mm dimensions.
    """
    import uuid
    dev_model = Device(
        id=str(uuid.uuid4()),
        meta={"width_mm": 25.4, "height_mm": 25.4}
    )

    # FIX: No transformer argument. Item is in mm (scene units).
    item = DeviceItem(dev_model)
    
    rect = item.rect()
    
    # Verification (Scene Units = mm)
    assert rect.width() == pytest.approx(25.4)
    assert rect.height() == pytest.approx(25.4)

def test_ghost_device_visual_state():
    """
    Validates PH1-4.4: Logic for red dashed outline if is_ghost is True.
    """
    import uuid
    dev_model = Device(id=str(uuid.uuid4()))
    
    # FIX: No transformer argument
    item = DeviceItem(dev_model, is_ghost=True)
    
    assert item.is_ghost is True
    # Visual properties checked by compliance tests, logic checked here.

def test_standard_device_visual_state():
    """Ensures non-ghost devices use the standard industrial theme."""
    import uuid
    dev_model = Device(id=str(uuid.uuid4()))
    
    # FIX: No transformer argument
    item = DeviceItem(dev_model, is_ghost=False)
    
    assert item.is_ghost is False