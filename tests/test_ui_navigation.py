import pytest
from ui.canvas import HarnessCanvas
from core.device import Device
from core.models import Harness
from api.manager import APIManager # Ensure API is initialized

# @pytest.mark.skip(reason="Feature pending refactor") # REMOVED
def test_zoom_extents(qtbot):
    """PH5-5.6: Zoom Extents should fit all items in view."""
    # Initialize API to prevent registry errors
    api = APIManager.get_instance()
    
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    canvas.show()
    qtbot.waitExposed(canvas)
    
    # Add items far apart
    harness = Harness()
    harness.devices.append(Device(id="D1", x=0, y=0))
    harness.devices.append(Device(id="D2", x=1000, y=1000))
    
    # Load into Canvas
    canvas.load_harness(harness)
    
    # Ensure items are added to scene
    assert len(canvas.scene.items()) >= 2
    
    # Check bounds BEFORE zoom (just to verify setup)
    initial_rect = canvas.scene.itemsBoundingRect()
    assert initial_rect.width() >= 1000
    
    # Call Zoom Extents
    canvas.zoom_extents()
    
    # Logic verification:
    # fitInView modifies the view's transform (scale).
    # We verify that the view's sceneRect or transform is valid.
    # But strictly, the test asks if the rect encompasses items.
    # The canvas.scene.itemsBoundingRect() is a property of the SCENE, independent of zoom.
    # So the assertion `rect.width() >= 1000` is actually verifying load_harness worked,
    # NOT that the zoom worked visually.
    # To verify zoom, we check the view transform.
    
    transform = canvas.transform()
    # If 1000x1000 items fit in a small widget (e.g. 640x480), scale must be < 1.0
    assert transform.m11() < 1.0 # m11 is X scale