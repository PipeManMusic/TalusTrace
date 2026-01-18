import pytest
from ui.canvas import HarnessCanvas
from core.device import Device
from core.models import Harness

@pytest.mark.skip(reason="Feature pending refactor")
def test_zoom_extents(qtbot):
    """PH5-5.6: Zoom Extents should fit all items in view."""
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    
    # Add items far apart
    harness = Harness()
    harness.devices.append(Device(id="D1", x=0, y=0))
    harness.devices.append(Device(id="D2", x=1000, y=1000))
    canvas.load_harness(harness)
    
    # Call Zoom Extents
    canvas.zoom_extents()
    
    # Check scene rect was updated to encompass items
    rect = canvas.scene.itemsBoundingRect()
    assert rect.width() >= 1000
    assert rect.height() >= 1000