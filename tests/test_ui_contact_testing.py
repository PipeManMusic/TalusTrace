import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from ui.canvas import HarnessCanvas
from core.device import Device
from ui.items.device import DeviceItem
from ui.items.wire import WireItem
from core.wire import Wire

@pytest.fixture
def canvas(qtbot):
    app = QApplication.instance() or QApplication([])
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    return canvas

def test_deviceitem_contact(canvas):
    device = Device(id="11111111-1111-1111-1111-111111111111", x=10, y=20, meta={"width_mm": 40, "height_mm": 30})
    item = DeviceItem(device)
    canvas.scene.addItem(item)
    # Test hit inside
    assert item.contains(item.boundingRect().center())
    # Test hit outside
    rect = item.boundingRect()
    outside = rect.bottomRight() + QPointF(rect.width(), rect.height())
    assert not item.contains(outside)

def test_wireitem_contact(canvas):
    wire = Wire(
        id="22222222-2222-2222-2222-222222222222",
        from_conn="11111111-1111-1111-1111-111111111111",
        from_pin="44444444-4444-4444-4444-444444444444",
        to_conn="33333333-3333-3333-3333-333333333333",
        to_pin="55555555-5555-5555-5555-555555555555",
        path_nodes=[(0,0),(100,0)]
    )
    item = WireItem(wire)
    canvas.scene.addItem(item)
    # Test hit near wire
    mid = item.path().pointAtPercent(0.5)
    assert item.contains(mid)
    # Test hit far from wire
    rect = item.boundingRect()
    far = mid + QPointF(rect.width()*2, rect.height()*2)
    assert not item.contains(far)
