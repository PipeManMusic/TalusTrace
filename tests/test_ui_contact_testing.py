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
    device = Device(id="D1", x=10, y=20, meta={"width_mm": 40, "height_mm": 30})
    item = DeviceItem(device)
    canvas.scene.addItem(item)
    # Test hit inside
    assert item.contains(item.boundingRect().center())
    # Test hit outside
    rect = item.boundingRect()
    outside = rect.bottomRight() + QPointF(rect.width(), rect.height())
    assert not item.contains(outside)

def test_wireitem_contact(canvas):
    wire = Wire(id="W1", from_conn="D1", from_pin="P1", to_conn="D2", to_pin="P2", path_nodes=[(0,0),(100,0)])
    item = WireItem(wire)
    canvas.scene.addItem(item)
    # Test hit near wire
    mid = item.path().pointAtPercent(0.5)
    assert item.contains(mid)
    # Test hit far from wire
    rect = item.boundingRect()
    far = mid + QPointF(rect.width()*2, rect.height()*2)
    assert not item.contains(far)
