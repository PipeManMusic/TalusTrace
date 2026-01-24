import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from ui.canvas import HarnessCanvas
from core.device import Device
from ui.items.device import DeviceItem
from core.wire import Wire
from ui.items.wire import WireItem
from ui.items.pin import PinItem

@pytest.fixture
def canvas(qtbot):
    app = QApplication.instance() or QApplication([])
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    return canvas

@pytest.mark.gui
def test_deviceitem_contact(canvas):
    device = Device(id="11111111-1111-1111-1111-111111111111", x=10, y=20, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    item = DeviceItem(device)
    canvas.scene.addItem(item)
    assert item.contains(item.boundingRect().center())
    rect = item.boundingRect()
    outside = rect.bottomRight() + QPointF(rect.width(), rect.height())
    assert not item.contains(outside)

@pytest.mark.gui
def test_wireitem_contact(canvas):
    wire = Wire(id="W1", from_conn="D1", from_pin="P1", to_conn="D2", to_pin="P2", path_nodes=[(0,0),(100,0)])
    item = WireItem(wire)
    canvas.scene.addItem(item)
    mid = item.path().pointAtPercent(0.5)
    assert item.contains(mid)
    rect = item.boundingRect()
    far = mid + QPointF(rect.width()*2, rect.height()*2)
    assert not item.contains(far)

@pytest.mark.gui
def test_pinitem_contact(canvas):
    from core.pin import Pin
    from core.enums import Side
    pin = Pin(id="P1", x=5, y=5, label="P1", side=Side.TOP)
    device = Device(id="D2", x=0, y=0, meta={"width_mm": 40, "height_mm": 30}, pins=[pin])
    item = DeviceItem(device)
    canvas.scene.addItem(item)
    # Find the pin item
    pin_item = None
    for child in item.childItems():
        if isinstance(child, PinItem):
            pin_item = child
            break
    assert pin_item is not None
    assert pin_item.contains(pin_item.boundingRect().center())
    rect = pin_item.boundingRect()
    outside = rect.bottomRight() + QPointF(rect.width(), rect.height())
    assert not pin_item.contains(outside)
