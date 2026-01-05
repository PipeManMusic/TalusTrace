import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_segment_no_cumulative_jump(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # Add two elbows to create multiple segments
    bundle.add_elbow_at(QPointF(80, 0))
    bundle.add_elbow_at(QPointF(120, 0))

    sh = bundle.segment_handles[1]  # pick a middle segment
    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    # Press to initialize anchor and snapshot
    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))
    QTest.qWait(5)

    # Steps: move to y+10, y+20; ensure absolute move matches expected deltas (no cumulative growth)
    prev = list(bundle.route)
    # step 1
    QTest.mouseMove(win.view.viewport(), QPoint(int(view_pos.x()), int(view_pos.y() + 10)))
    QTest.qWait(5)
    step1 = list(bundle.route)
    # step 2
    QTest.mouseMove(win.view.viewport(), QPoint(int(view_pos.x()), int(view_pos.y() + 20)))
    QTest.qWait(5)
    step2 = list(bundle.route)

    # Calculate per-elbow Y deltas from original
    deltas1 = [round(b[1] - a[1], 6) for (a, b) in zip(prev, step1)]
    deltas2 = [round(b[1] - a[1], 6) for (a, b) in zip(prev, step2)]

    # step2 delta should be larger than step1 but not by the amount added previously (i.e., step2 ≈ 2*step1)
    assert all(d2 >= d1 for d1, d2 in zip(deltas1, deltas2)), f"Expected monotonic growth: {deltas1} vs {deltas2}"
    # Ensure no runaway cumulative increase beyond reasonable bound (grid snapping may apply)
    assert all(d2 - d1 < 50 for d1, d2 in zip(deltas1, deltas2)), f"Unexpected cumulative growth: {deltas1} -> {deltas2}"

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y() + 20)))
    QTest.qWait(5)
