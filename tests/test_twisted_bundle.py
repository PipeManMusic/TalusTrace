import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtGui import QColor
from talustrace.frontend.items import TwistNodeItem, TwistedBundleItem, DeviceItem, WireItem
from talustrace.backend.models import Device, Wire, Side

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_wire_registers_with_twistnode(qapp):
    scene = QGraphicsScene()
    node = TwistNodeItem(on_changed=None)
    d_model = Device(id="D1", label="D1", pins=1, x=0, y=0)
    d_item = DeviceItem(d_model)

    scene.addItem(node)
    scene.addItem(d_item)

    # Create a wire that ends on the TwistNode 'H' pin. The device id used in the model string
    # is arbitrary for the node side because the visual node isn't backed by a Device model.
    wire_model = Wire(id="W1", from_conn="D1.1", to_conn="NODE.H")
    # Construct the visual wire: source is a device, target is the twist node
    wire_item = WireItem(wire_model, source_item=d_item, target_item=node)
    scene.addItem(wire_item)

    # The twist node should have recorded the wire under pin 'H'
    assert "H" in node.attached_wires
    assert wire_item in node.attached_wires["H"]


def test_twisted_bundle_inherits_colors(qapp):
    scene = QGraphicsScene()
    node_a = TwistNodeItem(on_changed=None)
    node_b = TwistNodeItem(on_changed=None)
    node_a.setPos(0, 0)
    node_b.setPos(200, 0)

    bundle = TwistedBundleItem(node_a, node_b, on_changed=None)
    bundle.update_geometry()

    # Create devices to connect to the node pins
    d1 = Device(id="D1", label="D1", pins=1, x=-40, y=0)
    d2 = Device(id="D2", label="D2", pins=1, x=240, y=0)
    from talustrace.frontend.items import DeviceItem, WireItem
    d1_item = DeviceItem(d1)
    d2_item = DeviceItem(d2)
    scene.addItem(d1_item)
    scene.addItem(d2_item)

    # Wire to node_a H with Red, wire to node_b L with Blue
    w1 = Wire(id="WA", from_conn="D1.1", to_conn="NODEA.H")
    w2 = Wire(id="WB", from_conn="D2.1", to_conn="NODEB.L")

    wire_a = WireItem(w1, source_item=d1_item, target_item=node_a)
    wire_b = WireItem(w2, source_item=d2_item, target_item=node_b)
    scene.addItem(wire_a)
    scene.addItem(wire_b)

    wire_a.set_color_code("RD")
    wire_b.set_color_code("BU")

    # Recompute bundle colors
    bundle.update_geometry()

    assert isinstance(bundle.color_a, QColor)
    assert isinstance(bundle.color_b, QColor)
    assert bundle.color_a == wire_a.pen().color()
    assert bundle.color_b == wire_b.pen().color()


def test_bundle_updates_when_wire_color_changes(qapp):
    node_a = TwistNodeItem(on_changed=None)
    node_b = TwistNodeItem(on_changed=None)
    bundle = TwistedBundleItem(node_a, node_b, on_changed=None)

    d = Device(id="D1", label="D1", pins=1)
    from talustrace.frontend.items import DeviceItem, WireItem
    d_item = DeviceItem(d)

    # Connect a wire to node_a.H
    w = Wire(id="W1", from_conn="D1.1", to_conn="NODE.H")
    w_item = WireItem(w, source_item=d_item, target_item=node_a)
    w_item.set_color_code("RD")
    bundle.update_geometry()
    assert bundle.color_a == w_item.pen().color()

    # Change color and ensure bundle updates
    w_item.set_color_code("BU")
    assert bundle.color_a == w_item.pen().color()
