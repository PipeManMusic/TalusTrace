import pytest
from PySide6.QtWidgets import QApplication

from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import WireItem
from talustrace.backend.models import Side, Wire


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    return app or QApplication([])


def test_delete_device_removes_wires_and_marks_dirty(qapp):
    win = MainWindow(restore_policy="skip")

    d1 = win.add_device(0, 0, label="A", pins=0, mark_dirty=False)
    d2 = win.add_device(40, 0, label="B", pins=0, mark_dirty=False)

    d1.add_pin_model(side=Side.RIGHT, label="p1", pin_id="1")
    d2.add_pin_model(side=Side.LEFT, label="p2", pin_id="2")

    wire_model = Wire(id="w1", from_conn=f"{d1.model.id}.1", to_conn=f"{d2.model.id}.2", color="RD")
    wire_item = WireItem(wire_model, source_item=d1, target_item=d2, on_changed=win.mark_dirty)
    win.scene.addItem(wire_item)
    win.wire_items.append(wire_item)

    win.mark_clean()
    win._delete_device_item(d1)

    assert d1 not in win.device_items
    assert wire_item not in win.wire_items
    assert wire_item not in d2.attached_wires
    assert d1.scene() is None
    assert wire_item.scene() is None
    assert win.dirty is True


def test_delete_pin_removes_attached_wires_and_marks_dirty(qapp):
    win = MainWindow(restore_policy="skip")

    d1 = win.add_device(0, 0, label="A", pins=0, mark_dirty=False)
    d2 = win.add_device(40, 0, label="B", pins=0, mark_dirty=False)

    d1.add_pin_model(side=Side.RIGHT, label="p1", pin_id="1")
    d2.add_pin_model(side=Side.LEFT, label="p2", pin_id="2")

    wire_model = Wire(id="w1", from_conn=f"{d1.model.id}.1", to_conn=f"{d2.model.id}.2", color="RD")
    wire_item = WireItem(wire_model, source_item=d1, target_item=d2, on_changed=win.mark_dirty)
    win.scene.addItem(wire_item)
    win.wire_items.append(wire_item)

    # Link wire to pins' devices
    d1.attached_wires.append(wire_item)
    d2.attached_wires.append(wire_item)

    win.mark_clean()
    win._delete_pin_item(d1, d1.pins["1"])

    assert d1.model.pins == []
    assert wire_item not in win.wire_items
    assert wire_item not in d1.attached_wires
    assert wire_item not in d2.attached_wires
    assert wire_item.scene() is None
    assert win.dirty is True


def test_delete_wire_removes_links_and_marks_dirty(qapp):
    win = MainWindow(restore_policy="skip")

    d1 = win.add_device(0, 0, label="A", pins=0, mark_dirty=False)
    d2 = win.add_device(40, 0, label="B", pins=0, mark_dirty=False)

    d1.add_pin_model(side=Side.RIGHT, label="p1", pin_id="1")
    d2.add_pin_model(side=Side.LEFT, label="p2", pin_id="2")

    wire_model = Wire(id="w1", from_conn=f"{d1.model.id}.1", to_conn=f"{d2.model.id}.2", color="RD")
    wire_item = WireItem(wire_model, source_item=d1, target_item=d2, on_changed=win.mark_dirty, on_delete=win._delete_wire_item)
    win.scene.addItem(wire_item)
    win.wire_items.append(wire_item)

    win.mark_clean()
    win._delete_wire_item(wire_item)

    assert wire_item not in win.wire_items
    assert wire_item not in d1.attached_wires
    assert wire_item not in d2.attached_wires
    assert wire_item.scene() is None
    assert win.dirty is True
