from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Side
from talustrace.frontend.items_baseline import GRID_SIZE


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_wire_elbow_interactive_drag_does_not_orphan():
    # Setup app and bundle+wire
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    b = win.add_twisted_bundle(200, 0)
    src_node = b.source_node

    d = win.add_device(0, 0, mark_dirty=False)
    d.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    win.handle_wire_creation(d.pins['1'], src_node.pins['H'])
    w = win.wire_items[-1]

    # Add two elbows
    w.add_elbow_at(QPointF(80, 0))
    w.add_elbow_at(QPointF(120, 0))

    # Press the first segment handle and drag it down by GRID_SIZE
    sh = w.segment_handles[0]
    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))
    QTest.qWait(50)

    moved = QPoint(int(view_pos.x()), int(view_pos.y() + GRID_SIZE))
    QTest.mouseMove(win.view.viewport(), moved)
    QTest.qWait(50)

    # Immediately after drag, handles must match route points
    for idx, h in enumerate(w.elbow_handles):
        route_pt = QPointF(*w.model.route[idx])
        handle_scene = h.mapToScene(h.boundingRect().center())
        _assert_close(handle_scene, route_pt)

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, moved)
    QTest.qWait(50)

    # Repeat for second segment
    sh2 = w.segment_handles[1]
    sh2_scene = sh2.mapToScene(sh2.boundingRect().center())
    view_pos2 = win.view.mapFromScene(sh2_scene)
    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos2.x()), int(view_pos2.y())))
    QTest.qWait(50)
    moved2 = QPoint(int(view_pos2.x() - GRID_SIZE), int(view_pos2.y()))
    QTest.mouseMove(win.view.viewport(), moved2)
    QTest.qWait(50)
    for idx, h in enumerate(w.elbow_handles):
        route_pt = QPointF(*w.model.route[idx])
        handle_scene = h.mapToScene(h.boundingRect().center())
        _assert_close(handle_scene, route_pt)
    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, moved2)
