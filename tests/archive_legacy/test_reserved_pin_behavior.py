import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import TwistNodeItem, TwistedBundleItem
from talustrace.backend.models import Device

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_reserved_side_blocks_connection(qapp):
    win = MainWindow(restore_policy='skip')
    # Add one bundle with nodes and ensure node records reserved side
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a, b = bundle.source_node, bundle.target_node
    assert hasattr(a, '_bundle_side') and a._bundle_side is not None

    # Try to connect a device to a pin on the reserved side and ensure no wire is created
    d = Device(id='D1', label='D1', pins=1)
    d_item = win.add_device(200, 0, label='D1', pins=1, mark_dirty=False)

    # Find a pin on the reserved side of node 'a'
    reserved_pins = [p for p in a.pins.values() if p.model.side == a._bundle_side]
    assert reserved_pins, 'No reserved pins found on node'
    reserved_pin = reserved_pins[0]

    # Try to create a wire to the reserved pin
    start_pin = d_item.pins['1']
    end_pin = reserved_pin
    win.handle_wire_creation(start_pin, end_pin)

    # No new wires should have been added
    assert len(win.wire_items) == 0
