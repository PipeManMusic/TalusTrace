from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Side


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_wire_elbow_remains_attached_after_segment_move():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    d1 = win.add_device(0, 0, mark_dirty=False)
    d2 = win.add_device(200, 0, mark_dirty=False)
    d1.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    d2.add_pin_model(side=Side.LEFT, label='p2', pin_id='2')

    win.handle_wire_creation(d1.pins['1'], d2.pins['2'])
    w = win.wire_items[-1]

    # Add two elbows between devices so there are two route points
    w.add_elbow_at(QPointF(80, 0))
    w.add_elbow_at(QPointF(120, 0))
    assert len(w.model.route) == 2

    # Move the first segment (segment_index=0) down by 1 grid step
    nodes = w._build_nodes()
    seg_idx = 0
    anchor_mid = QPointF((nodes[seg_idx].x() + nodes[seg_idx+1].x())/2, (nodes[seg_idx].y() + nodes[seg_idx+1].y())/2)
    new_mid = QPointF(anchor_mid.x(), anchor_mid.y() + 20)
    orig_route = list(w.model.route)

    w.move_segment_handle(seg_idx, new_mid, anchor_mid, original_route=orig_route)

    # After the move all elbow handles must match the model route points
    for idx, h in enumerate(w.elbow_handles):
        route_pt = QPointF(*w.model.route[idx])
        handle_scene = h.mapToScene(h.boundingRect().center())
        _assert_close(handle_scene, route_pt)

    # Now move the other segment (segment_index=1) left by 20 px and check again
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
