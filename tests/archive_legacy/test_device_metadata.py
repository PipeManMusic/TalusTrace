import pytest
from PySide6.QtWidgets import QApplication

from talustrace.frontend.items import DeviceItem, WireItem
from talustrace.backend.models import Device, Wire


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    return app or QApplication([])


def test_edit_device_updates_wire_refs(qapp):
    dev_a = Device(id="A", label="A", pins=[{"id": "1", "side": "left"}])
    dev_b = Device(id="B", label="B", pins=[{"id": "1", "side": "right"}])

    item_a = DeviceItem(dev_a)
    item_b = DeviceItem(dev_b)

    wire_model = Wire(id="W1", from_conn="A.1", to_conn="B.1")
    wire_item = WireItem(wire_model, source_item=item_a, target_item=item_b)

    item_a.attached_wires.append(wire_item)
    item_b.attached_wires.append(wire_item)

    item_a.apply_device_edit(new_id="A2", new_label="New Label")

    assert item_a.model.id == "A2"
    assert item_a.model.label == "New Label"
    assert wire_item.model.from_conn == "A2.1"
    assert wire_item.src_pin_id == "1"
    assert item_a.id_text.text() == "(A2)"
    assert item_a.label.text() == "New Label"
