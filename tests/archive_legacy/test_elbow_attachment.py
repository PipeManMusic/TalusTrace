from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPoint, QPointF
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Side
from talustrace.frontend.items_baseline import GRID_SIZE


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_elbow_handles_follow_wire_after_device_move():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    d1 = win.add_device(0, 0, mark_dirty=False)
    d2 = win.add_device(200, 0, mark_dirty=False)
    d1.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    d2.add_pin_model(side=Side.LEFT, label='p2', pin_id='2')
    win.handle_wire_creation(d1.pins['1'], d2.pins['2'])
    w = win.wire_items[-1]

    # add elbows
    w.add_elbow_at(QPointF(80, 0))
    w.add_elbow_at(QPointF(120, 0))

    # initial check: handle scene positions equal route points
    for idx, h in enumerate(w.elbow_handles):
        route_pt = QPointF(*w.model.route[idx])
        handle_scene = h.mapToScene(h.boundingRect().center())
        _assert_close(handle_scene, route_pt)

    # Move device d1 by one grid step and ensure elbows remain at the same absolute positions
    new_pos = d1.pos() + QPointF(GRID_SIZE, GRID_SIZE)
    d1.setPos(new_pos)

    # No explicit wait — itemChange triggers wire.update_geometry synchronously
    win.scene.update()

    for idx, h in enumerate(w.elbow_handles):
        route_pt = QPointF(*w.model.route[idx])
        handle_scene = h.mapToScene(h.boundingRect().center())
        _assert_close(handle_scene, route_pt)
