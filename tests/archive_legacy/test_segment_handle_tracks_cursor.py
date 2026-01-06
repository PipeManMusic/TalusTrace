import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import GRID_SIZE

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _assert_close(a, b, tol=4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_wire_segment_handle_tracks_cursor(qapp):
    win = MainWindow(restore_policy='skip')
    d1 = win.add_device(0, 0, mark_dirty=False)
    d2 = win.add_device(200, 0, mark_dirty=False)
    from talustrace.backend.models import Side
    d1.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    d2.add_pin_model(side=Side.LEFT, label='p2', pin_id='2')
    win.handle_wire_creation(d1.pins['1'], d2.pins['2'])
    w = win.wire_items[-1]

    w.add_elbow_at(QPointF(80, 0))
    w.add_elbow_at(QPointF(120, 0))
    sh = w.segment_handles[1]

    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))
    QTest.qWait(50)

    for dx, dy in [(0, 30), (0, -30), (30, 0), (-30, 0)]:
        moved = QPoint(int(view_pos.x() + dx), int(view_pos.y() + dy))
        QTest.mouseMove(win.view.viewport(), moved)
        QTest.qWait(50)
        cursor_scene = win.view.mapToScene(moved)
        # Expect grip to snap to grid, so compute snapped cursor location
        snapped_cursor = QPointF(round(cursor_scene.x() / GRID_SIZE) * GRID_SIZE, round(cursor_scene.y() / GRID_SIZE) * GRID_SIZE)
        handle_scene = sh.mapToScene(sh.boundingRect().center())
        _assert_close(handle_scene, snapped_cursor)

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, moved)


def test_twisted_pair_segment_handle_tracks_cursor(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    bundle.add_elbow_at(QPointF(80, 0))
    bundle.add_elbow_at(QPointF(120, 0))
    sh = bundle.segment_handles[1]

    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))
    QTest.qWait(50)

    for dx, dy in [(0, 30), (0, -30), (30, 0), (-30, 0)]:
        moved = QPoint(int(view_pos.x() + dx), int(view_pos.y() + dy))
        QTest.mouseMove(win.view.viewport(), moved)
        QTest.qWait(50)
        cursor_scene = win.view.mapToScene(moved)
        # Expect grip to snap to grid, so compute snapped cursor location
        snapped_cursor = QPointF(round(cursor_scene.x() / GRID_SIZE) * GRID_SIZE, round(cursor_scene.y() / GRID_SIZE) * GRID_SIZE)
        handle_scene = sh.mapToScene(sh.boundingRect().center())
        _assert_close(handle_scene, snapped_cursor)

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, moved)
