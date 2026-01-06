from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Side


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_wire_elbow_stress_drag_no_orphan():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    # Setup bundle + wire + elbows
    b = win.add_twisted_bundle(200, 0)
    src_node = b.source_node
    d = win.add_device(0, 0, mark_dirty=False)
    d.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    win.handle_wire_creation(d.pins['1'], src_node.pins['H'])
    w = win.wire_items[-1]

    w.add_elbow_at(QPointF(80, 0))
    w.add_elbow_at(QPointF(120, 0))

    # Press the first segment handle and perform many small moves to simulate a long drag
    sh = w.segment_handles[0]
    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))

    # simulate 20 small downward moves of 1px each
    for i in range(20):
        moved = QPoint(int(view_pos.x()), int(view_pos.y() + (i+1)))
        QTest.mouseMove(win.view.viewport(), moved)
        QTest.qWait(10)
        # After each move ensure elbow handles match route points
        for idx, h in enumerate(w.elbow_handles):
            route_pt = QPointF(*w.model.route[idx])
            handle_scene = h.mapToScene(h.boundingRect().center())
            _assert_close(handle_scene, route_pt)

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y()+20)))
