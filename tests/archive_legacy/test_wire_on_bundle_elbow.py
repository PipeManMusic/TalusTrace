from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Side


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_wire_attached_to_bundle_node_elbows_follow_segment_moves():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    # Create bundle (creates two TwistNodeItems)
    b = win.add_twisted_bundle(200, 0)
    src_node = b.source_node

    # Add a device and connect it to the source node H pin
    d = win.add_device(0, 0, mark_dirty=False)
    d.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    win.handle_wire_creation(d.pins['1'], src_node.pins['H'])
    w = win.wire_items[-1]

    # Add two elbows on the wire
    w.add_elbow_at(QPointF(80, 0))
    w.add_elbow_at(QPointF(120, 0))
    assert len(w.model.route) == 2

    # Move first segment down by 20
    nodes = w._build_nodes()
    seg_idx = 0
    anchor_mid = QPointF((nodes[seg_idx].x() + nodes[seg_idx+1].x())/2, (nodes[seg_idx].y() + nodes[seg_idx+1].y())/2)
    new_mid = QPointF(anchor_mid.x(), anchor_mid.y() + 20)
    orig_route = list(w.model.route)
    w.move_segment_handle(seg_idx, new_mid, anchor_mid, original_route=orig_route)

    # after move, elbow handles must track model.route
    for idx, h in enumerate(w.elbow_handles):
        route_pt = QPointF(*w.model.route[idx])
        handle_scene = h.mapToScene(h.boundingRect().center())
        _assert_close(handle_scene, route_pt)

    # Move second segment left by 20
    nodes = w._build_nodes()
    seg_idx = 1
    anchor_mid = QPointF((nodes[seg_idx].x() + nodes[seg_idx+1].x())/2, (nodes[seg_idx].y() + nodes[seg_idx+1].y())/2)
    new_mid = QPointF(anchor_mid.x() - 20, anchor_mid.y())
    orig_route = list(w.model.route)
    w.move_segment_handle(seg_idx, new_mid, anchor_mid, original_route=orig_route)

    for idx, h in enumerate(w.elbow_handles):
        route_pt = QPointF(*w.model.route[idx])
        handle_scene = h.mapToScene(h.boundingRect().center())
        _assert_close(handle_scene, route_pt)
