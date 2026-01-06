import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtGui import QColor
from PySide6.QtCore import QPointF
from talustrace.backend.models import Device, Wire, Side
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import DeviceItem, WireItem

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_wire_geometry_update(qapp):
    scene = QGraphicsScene()
    
    # 1. Create Devices
    d1_model = Device(id="D1", label="Dev1", pins=2, x=0, y=0)
    d2_model = Device(id="D2", label="Dev2", pins=2, x=100, y=0)
    
    d1_item = DeviceItem(d1_model)
    d2_item = DeviceItem(d2_model)
    
    scene.addItem(d1_item)
    scene.addItem(d2_item)
    
    # 2. Create Wire connecting D1.1 to D2.1
    # Note: Pin IDs are generated as "1", "2" etc.
    wire_model = Wire(id="W1", from_conn="D1.1", to_conn="D2.1")
    wire_item = WireItem(wire_model, source_item=d1_item, target_item=d2_item)
    scene.addItem(wire_item)
    
    # 3. Check initial geometry
    path = wire_item.path()
    assert not path.isEmpty()
    end_elem = path.elementAt(path.elementCount() - 1)
    initial_p2 = QPointF(end_elem.x, end_elem.y)
    
    # 4. Move D2
    d2_item.setPos(200, 0)
    
    # 5. Check if wire updated
    # We need to manually trigger the update or rely on the signal if connected
    # DeviceItem.itemChange calls update_geometry on attached wires
    
    # Since we setPos directly, itemChange should be called by Qt
    
    wire_item.update_geometry()
    end_new = wire_item.path().elementAt(wire_item.path().elementCount() - 1)
    assert end_new.x > initial_p2.x()


def test_elbow_insert_move_delete(qapp):
    scene = QGraphicsScene()
    d1_model = Device(id="D1", label="Dev1", pins=2, x=0, y=0)
    d2_model = Device(id="D2", label="Dev2", pins=2, x=100, y=0)
    d1_item = DeviceItem(d1_model)
    d2_item = DeviceItem(d2_model)
    scene.addItem(d1_item)
    scene.addItem(d2_item)

    wire_model = Wire(id="W1", from_conn="D1.1", to_conn="D2.1")
    wire_item = WireItem(wire_model, source_item=d1_item, target_item=d2_item)
    scene.addItem(wire_item)

    wire_item.add_elbow_at(QPointF(40, 0))
    assert len(wire_item.model.route) == 1
    assert wire_item.model.route[0] == (40.0, 0.0)

    wire_item.move_elbow(0, QPointF(40, 20))
    assert wire_item.model.route[0] == (40.0, 20.0)

    wire_item.add_elbow_at(QPointF(80, 0))
    assert len(wire_item.model.route) == 2

    wire_item.delete_elbow(0)
    assert len(wire_item.model.route) == 1


def test_change_wire_color_updates_model_and_pen(qapp):
    scene = QGraphicsScene()
    d1_model = Device(id="D1", label="Dev1", pins=2, x=0, y=0)
    d2_model = Device(id="D2", label="Dev2", pins=2, x=100, y=0)
    d1_item = DeviceItem(d1_model)
    d2_item = DeviceItem(d2_model)
    scene.addItem(d1_item)
    scene.addItem(d2_item)

    wire_model = Wire(id="W1", from_conn="D1.1", to_conn="D2.1", color="RD")
    wire_item = WireItem(wire_model, source_item=d1_item, target_item=d2_item)
    scene.addItem(wire_item)

    wire_item.set_color_code("GN")

    assert wire_item.model.color == "GN"
    assert wire_item.pen().color().name().lower() == QColor(0, 255, 0).name().lower()

    wire_item.set_color_code("BN")
    assert wire_item.model.color == "BN"
    assert wire_item.pen().color().name().lower() == QColor(165, 42, 42).name().lower()


def test_wire_metadata_inherits_from_pins(qapp):
    scene = QGraphicsScene()
    d1_model = Device(id="D1", label="Dev1", pins=2, x=0, y=0)
    d2_model = Device(id="D2", label="Dev2", pins=2, x=100, y=0)
    d1_item = DeviceItem(d1_model)
    d2_item = DeviceItem(d2_model)
    scene.addItem(d1_item)
    scene.addItem(d2_item)

    # Add pin metadata
    d1_item.pins["1"].set_meta({"function": "sense", "voltage": "5V"})
    d2_item.pins["1"].set_meta({"function": "sense", "shield": "yes"})

    wire_model = Wire(id="W1", from_conn="D1.1", to_conn="D2.1", color="RD")
    wire_item = WireItem(wire_model, source_item=d1_item, target_item=d2_item)
    scene.addItem(wire_item)

    wire_item.refresh_metadata()
    assert wire_item.model.meta["function"] == "sense"
    assert wire_item.model.meta["voltage"] == "5V"
    assert wire_item.model.meta["shield"] == "yes"


def test_mainwindow_wire_creation_merges_pin_meta(qapp):
    win = MainWindow(restore_policy="skip")

    d1 = win.add_device(0, 0, label="A", pins=0, mark_dirty=False)
    d2 = win.add_device(40, 0, label="B", pins=0, mark_dirty=False)

    d1.add_pin_model(side=Side.RIGHT, label="p1", pin_id="1")
    d2.add_pin_model(side=Side.LEFT, label="p2", pin_id="2")

    d1.pins["1"].set_meta({"function": "sense", "voltage": "5V"})
    d2.pins["2"].set_meta({"function": "sense", "shield": "yes"})

    win.handle_wire_creation(d1.pins["1"], d2.pins["2"])

    wire_item = win.wire_items[-1]
    assert wire_item.model.meta["function"] == "sense"
    assert wire_item.model.meta["voltage"] == "5V"
    assert wire_item.model.meta["shield"] == "yes"


def test_wire_metadata_updates_when_pin_meta_changes(qapp):
    win = MainWindow(restore_policy="skip")

    d1 = win.add_device(0, 0, label="A", pins=0, mark_dirty=False)
    d2 = win.add_device(40, 0, label="B", pins=0, mark_dirty=False)

    d1.add_pin_model(side=Side.RIGHT, label="p1", pin_id="1")
    d2.add_pin_model(side=Side.LEFT, label="p2", pin_id="2")

    win.handle_wire_creation(d1.pins["1"], d2.pins["2"])
    wire_item = win.wire_items[-1]

    d1.pins["1"].set_meta({"function": "sense", "voltage": "5V"})
    d2.pins["2"].set_meta({"shield": "yes"})

    assert wire_item.model.meta["function"] == "sense"
    assert wire_item.model.meta["voltage"] == "5V"
    assert wire_item.model.meta["shield"] == "yes"


def test_wire_tooltip_includes_labels_and_meta(qapp):
    scene = QGraphicsScene()
    d1_model = Device(id="D1", label="Dev One", pins=2, x=0, y=0)
    d2_model = Device(id="D2", label="Dev Two", pins=2, x=100, y=0)
    d1_item = DeviceItem(d1_model)
    d2_item = DeviceItem(d2_model)
    scene.addItem(d1_item)
    scene.addItem(d2_item)

    d1_item.pins["1"].set_meta({"function": "sense"})
    d2_item.pins["1"].set_meta({"shield": "yes"})

    wire_model = Wire(id="W1", from_conn="D1.1", to_conn="D2.1", color="RD")
    wire_item = WireItem(wire_model, source_item=d1_item, target_item=d2_item)
    scene.addItem(wire_item)
    wire_item.refresh_metadata()

    tip = wire_item.toolTip()
    assert "Dev One" in tip
    assert "Dev Two" in tip
    assert "function" in tip
    assert "shield" in tip
    
