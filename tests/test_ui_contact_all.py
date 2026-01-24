import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from ui.canvas import HarnessCanvas
from core.device import Device
from ui.items.device import DeviceItem
from core.wire import Wire
from ui.items.wire import WireItem
from ui.items.pin import PinItem
from ui.items.segment_grip import SegmentGripItem
from ui.items.elbow_grip import ElbowGripItem
from core.pin import Pin
from core.enums import Side

@pytest.fixture
def canvas(qtbot):
    app = QApplication.instance() or QApplication([])
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    return canvas

def test_deviceitem_contact(canvas):
    device = Device(id="11111111-1111-1111-1111-111111111111", x=10, y=20, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    item = DeviceItem(device)
    canvas.scene.addItem(item)
    assert item.contains(item.boundingRect().center())
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
    mid = item.path().pointAtPercent(0.5)
    assert item.contains(mid)
    rect = item.boundingRect()
    far = mid + QPointF(rect.width()*2, rect.height()*2)
    assert not item.contains(far)

def test_pinitem_contact(canvas):
    pin = Pin(id="44444444-4444-4444-4444-444444444444", x=5, y=5, label="44444444-4444-4444-4444-444444444444", side=Side.TOP)
    device = Device(id="33333333-3333-3333-3333-333333333333", x=0, y=0, meta={"width_mm": 40, "height_mm": 30}, pins=[pin])
    item = DeviceItem(device)
    canvas.scene.addItem(item)
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

def test_segmentgripitem_contact(canvas):
    wire = Wire(
        id="66666666-6666-6666-6666-666666666666",
        from_conn="11111111-1111-1111-1111-111111111111",
        from_pin="44444444-4444-4444-4444-444444444444",
        to_conn="33333333-3333-3333-3333-333333333333",
        to_pin="55555555-5555-5555-5555-555555555555",
        path_nodes=[(0,0),(100,0)]
    )
    wire_item = WireItem(wire)
    canvas.scene.addItem(wire_item)
    grip = SegmentGripItem(wire_item, 0, 1, (0,0), (100,0))
    canvas.scene.addItem(grip)
    assert grip.contains(grip.boundingRect().center())
    rect = grip.boundingRect()
    outside = rect.bottomRight() + QPointF(rect.width(), rect.height())
    assert not grip.contains(outside)

def test_elbowgripitem_contact(canvas):
    wire = Wire(
        id="77777777-7777-7777-7777-777777777777",
        from_conn="11111111-1111-1111-1111-111111111111",
        from_pin="44444444-4444-4444-4444-444444444444",
        to_conn="33333333-3333-3333-3333-333333333333",
        to_pin="55555555-5555-5555-5555-555555555555",
        path_nodes=[(0,0),(100,0)]
    )
    wire_item = WireItem(wire)
    canvas.scene.addItem(wire_item)
    grip = ElbowGripItem(wire_item, 0, (0,0))
    canvas.scene.addItem(grip)
    assert grip.contains(grip.boundingRect().center())
    rect = grip.boundingRect()
    outside = rect.bottomRight() + QPointF(rect.width(), rect.height())
    assert not grip.contains(outside)
