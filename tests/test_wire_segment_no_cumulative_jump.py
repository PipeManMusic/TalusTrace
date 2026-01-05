import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_wire_segment_no_cumulative_jump(qapp):
    win = MainWindow(restore_policy='skip')
    # create two devices and a wire between them via MainWindow helper
    d1 = win.add_device(0, 0, mark_dirty=False)
    d2 = win.add_device(200, 0, mark_dirty=False)
    # Add pins and create wire via the normal UI helper so handles are created
    from talustrace.backend.models import Side
    d1.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    d2.add_pin_model(side=Side.LEFT, label='p2', pin_id='2')
    win.handle_wire_creation(d1.pins['1'], d2.pins['2'])
    w = win.wire_items[-1]

    # add two elbows on the wire
    w.add_elbow_at(QPointF(80, 0))
    w.add_elbow_at(QPointF(120, 0))

    sh = w.segment_handles[1]
    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    # Press to initialize anchor and snapshot
    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))
    QTest.qWait(5)

    prev = list(w.model.route)
    # step 1
    QTest.mouseMove(win.view.viewport(), QPoint(int(view_pos.x()), int(view_pos.y() + 10)))
    QTest.qWait(5)
    step1 = list(w.model.route)
    # step 2
    QTest.mouseMove(win.view.viewport(), QPoint(int(view_pos.x()), int(view_pos.y() + 20)))
    QTest.qWait(5)
    step2 = list(w.model.route)

    # deltas should be monotonic and not runaway
    deltas1 = [round(b[1] - a[1], 6) for (a, b) in zip(prev, step1)]
    deltas2 = [round(b[1] - a[1], 6) for (a, b) in zip(prev, step2)]

    assert all(d2 >= d1 for d1, d2 in zip(deltas1, deltas2)), f"Expected monotonic growth: {deltas1} vs {deltas2}"
    assert all(d2 - d1 < 50 for d1, d2 in zip(deltas1, deltas2)), f"Unexpected cumulative growth: {deltas1} -> {deltas2}"

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y() + 20)))
    QTest.qWait(5)
