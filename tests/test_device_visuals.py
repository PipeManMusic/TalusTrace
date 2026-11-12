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


# A minimal, valid SVG with a portrait 100x200 viewBox (aspect 0.5).
_PORTRAIT_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 200">'
    '<rect x="0" y="0" width="100" height="200" fill="#123456"/></svg>'
)


def test_svg_target_rect_preserves_aspect_on_landscape_device(qtbot):
    """A portrait SVG dropped into a landscape device rect must not stretch.

    The target rect the SVG renders into should keep the SVG's aspect ratio
    (0.5) and be centred inside the device rect (letterboxed), never filling
    the full mismatched rect.
    """
    import uuid
    dev_model = Device(
        id=str(uuid.uuid4()),
        meta={"width_mm": 40.0, "height_mm": 20.0},  # landscape, aspect 2.0
        svg_body=_PORTRAIT_SVG,
    )
    item = DeviceItem(dev_model)
    assert item._svg_renderer is not None and item._svg_renderer.isValid()

    target = item._svg_target_rect()
    device_rect = item.rect()

    # Aspect ratio of the render target must match the SVG viewBox (0.5),
    # NOT the device rect (2.0).
    assert target.width() / target.height() == pytest.approx(0.5, rel=1e-3)
    # Portrait art in a landscape rect is height-constrained.
    assert target.height() == pytest.approx(device_rect.height(), rel=1e-3)
    assert target.width() < device_rect.width()
    # Centred horizontally within the device rect.
    left_margin = target.x() - device_rect.x()
    right_margin = (device_rect.x() + device_rect.width()) - (target.x() + target.width())
    assert left_margin == pytest.approx(right_margin, rel=1e-3)


def test_svg_target_rect_defaults_to_full_rect_without_svg(qtbot):
    """Without an SVG the render target is just the device rect (no-op)."""
    import uuid
    dev_model = Device(id=str(uuid.uuid4()), meta={"width_mm": 30.0, "height_mm": 30.0})
    item = DeviceItem(dev_model)
    assert item._svg_target_rect() == item.rect()