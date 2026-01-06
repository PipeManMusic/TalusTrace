from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.items_baseline import WireItem
from talustrace.backend.models import Wire


def test_projection_on_straight_wire():
    app = QApplication.instance() or QApplication([])
    # Create a straight horizontal wire from (0,0) to (200,0)
    w = Wire(id='W1', **{'from': 'D1.1', 'to': 'D2.1'})
    w.route = []
    wire_item = WireItem(w)
    # Monkey-patch _build_nodes to return our explicit nodes (scene coords)
    wire_item._build_nodes = lambda: [QPointF(0, 0), QPointF(200, 0)]

    t, pt, seg = wire_item.calculate_snap_to_polyline(QPointF(100, 10))
    assert abs(t - 0.5) < 0.02
    assert abs(pt.y() - 0.0) < 0.01


def test_projection_clamps_and_segments():
    app = QApplication.instance() or QApplication([])
    w = Wire(id='W2', **{'from': 'D1.1', 'to': 'D2.1'})
    w.route = [(100, 0)]  # two segments: 0->100, 100->end
    wire_item = WireItem(w)
    wire_item._build_nodes = lambda: [QPointF(0, 0), QPointF(100, 0), QPointF(200, 0)]

    # Point near second segment at x=150,y=20 should project near t~0.75
    t, pt, seg = wire_item.calculate_snap_to_polyline(QPointF(150, 20))
    assert seg == 1
    assert abs(t - 0.75) < 0.03

    # Point beyond end clamps to t=1
    t2, pt2, seg2 = wire_item.calculate_snap_to_polyline(QPointF(300, 0))
    assert abs(t2 - 1.0) < 1e-6
    assert seg2 == 1
