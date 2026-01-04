import pytest
from PySide6.QtWidgets import QApplication

from talustrace.frontend.items import DeviceItem, PIN_PITCH
from talustrace.backend.models import Device, Side


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    return app or QApplication([])


def test_add_pin_single(qapp):
    changed = {"dirty": False}
    dev = Device(id="D1", label="Dev", pins=0)

    def mark():
        changed["dirty"] = True

    item = DeviceItem(dev, on_changed=mark)
    item.add_pin_model(side=Side.LEFT, label="L1", pin_id="1")

    assert len(dev.pins) == 1
    assert dev.pins[0].side == Side.LEFT
    assert dev.pins[0].label == "L1"
    assert changed["dirty"] is True


def test_bulk_pins_alternate_sides(qapp):
    dev = Device(id="D1", label="Dev", pins=0)
    item = DeviceItem(dev)

    for i in range(4):
        side = Side.LEFT if i % 2 == 0 else Side.RIGHT
        item.add_pin_model(side=side, label=None, pin_id=str(i + 1))

    sides = [p.side for p in dev.pins]
    assert sides == [Side.LEFT, Side.RIGHT, Side.LEFT, Side.RIGHT]
    assert len(item.pins) == 4


def test_pin_layout_centered_vertically(qapp):
    dev = Device(id="D2", label="Device", pins=0)
    item = DeviceItem(dev)

    # add multiple pins on both sides to force vertical centering logic
    for i in range(6):
        item.add_pin_model(side=Side.LEFT if i % 2 == 0 else Side.RIGHT, label=None, pin_id=str(i + 1))

    ys = [pin.pos().y() for pin in item.pins.values()]
    rect_height = item.rect().height()

    assert min(ys) >= 0
    assert max(ys) <= rect_height

    label_center = item.label.pos().y() + item.label.boundingRect().height() / 2
    mid_y = sum(ys) / len(ys)
    assert abs(mid_y - label_center) <= PIN_PITCH / 2
