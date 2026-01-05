from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_bundle_elbow_stress_drag_no_orphan():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    # Create bundle and add an elbow
    b = win.add_twisted_bundle(200, 0)
    b.add_elbow_at(QPointF(100, 0))

    # Pick the first segment handle and perform many 1px moves downward
    sh = b.segment_handles[0]
    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))

    for i in range(40):
        moved = QPoint(int(view_pos.x()), int(view_pos.y() + (i+1)))
        QTest.mouseMove(win.view.viewport(), moved)
        QTest.qWait(10)
        # After each tiny move, assert that elbows remain attached to route
        for idx, h in enumerate(b.elbow_handles):
            route_pt = QPointF(*b.route[idx])
            handle_scene = h.mapToScene(h.boundingRect().center())
            _assert_close(handle_scene, route_pt)

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y()+40)))
