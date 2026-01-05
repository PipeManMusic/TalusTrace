from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Side
from talustrace.frontend.items_baseline import GRID_SIZE


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_bundle_elbow_moves_with_segment_move():
    # Create an application context if needed
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    # Create a bundle (helper creates nodes)
    b = win.add_twisted_bundle(0, 0)

    # Add an elbow in the middle
    b.add_elbow_at(QPointF(100, 0))
    assert len(b.route) == 1

    # Find a segment handle that sits adjacent to the elbow (usually segment index 1)
    # Move that segment by delta (simulate drag)
    pts = b._poly_points()
    # choose segment 1 if available else 0
    seg_idx = 1 if len(pts) > 2 else 0
    orig_route = list(b.route)
    anchor_mid = QPointF((pts[seg_idx].x() + pts[seg_idx+1].x())/2, (pts[seg_idx].y() + pts[seg_idx+1].y())/2)

    # Move segment down by GRID_SIZE
    new_mid = QPointF(anchor_mid.x(), anchor_mid.y() + GRID_SIZE)
    b.move_segment_handle(seg_idx, new_mid, anchor_mid, original_route=orig_route)

    # After move, route should have been updated and elbow handle moved accordingly
    for idx, (x,y) in enumerate(b.route):
        route_pt = QPointF(x,y)
        handle_scene = b.elbow_handles[idx].mapToScene(b.elbow_handles[idx].boundingRect().center())
        _assert_close(handle_scene, route_pt)
