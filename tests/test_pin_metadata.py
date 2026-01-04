import pytest
from PySide6.QtWidgets import QApplication

from talustrace.frontend.items import DeviceItem, WireItem
from talustrace.backend.models import Device, Wire, Side


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    return app or QApplication([])


def test_edit_pin_updates_wire_refs(qapp):
    dev_a = Device(id="A", label="A", pins=[{"id": "1", "side": "left"}])
    dev_b = Device(id="B", label="B", pins=[{"id": "1", "side": "right"}])

    item_a = DeviceItem(dev_a)
    item_b = DeviceItem(dev_b)

    wire_model = Wire(id="W1", from_conn="A.1", to_conn="B.1")
    wire_item = WireItem(wire_model, source_item=item_a, target_item=item_b)

    item_a.attached_wires.append(wire_item)
    item_b.attached_wires.append(wire_item)

    # Apply edit without dialogs
    pin_item = item_a.pins["1"]
    item_a.apply_pin_edit(pin_item, new_id="2", new_label="New", new_side=Side.RIGHT)

    assert wire_item.src_pin_id == "2"
    assert wire_item.model.from_conn == "A.2"
    assert item_a.model.pins[0].id == "2"
    assert item_a.model.pins[0].side == Side.RIGHT
