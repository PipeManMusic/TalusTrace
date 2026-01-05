import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Device

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_bundle_deletion_clears_reserved_side_and_removes_bundle(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a, b = bundle.source_node, bundle.target_node
    assert hasattr(a, '_bundle_side') and a._bundle_side is not None
    # Delete via app helper
    win._delete_bundle_item(bundle)
    assert bundle not in win.bundle_items
    assert bundle.scene() is None
    assert getattr(a, '_bundle_side', None) is None


def test_connect_two_wires_on_non_bundle_side(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a, b = bundle.source_node, bundle.target_node

    # Find two connectable pins on node a (they should be H and L on non-bundle side)
    connectable = [p for p in a.pins.values() if a.pin_connectable(p.model.id)]
    assert len(connectable) >= 2

    # Add a device and connect two wires to a's H and L
    d = Device(id='D1', label='D1', pins=2)
    d_item = win.add_device(200, 0, label='D', pins=2, mark_dirty=False)

    # Connect to two distinct connectable pins
    start_pins = [d_item.pins['1'], d_item.pins['2']]
    target_pins = connectable[:2]

    # Connect first wire
    win.handle_wire_creation(start_pins[0], target_pins[0])
    # Connect second
    win.handle_wire_creation(start_pins[1], target_pins[1])

    assert len(win.wire_items) == 2
