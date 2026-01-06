import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_segment_stable_drag(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # Add two elbows to create multiple segments
    bundle.add_elbow_at(QPointF(80, 0))
    bundle.add_elbow_at(QPointF(120, 0))

    sh = bundle.segment_handles[1]  # pick a middle segment
    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    # Simulate press
    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))
    QTest.qWait(5)

    # Multiple moves large enough to cross grid snapping; ensure the route changes smoothly (no huge jumps)
    prev_route = list(bundle.route)
    for dy in (25, 50, 75):
        QTest.mouseMove(win.view.viewport(), QPoint(int(view_pos.x()), int(view_pos.y() + dy)))
        QTest.qWait(5)
        # route should have changed relative to previous but not wildly
        assert bundle.route != prev_route
        # Ensure per-step movement is modest (no teleport)
        # Compare y deltas for matching x coords
        paired = [(a, b) for (a, b) in zip(prev_route, bundle.route) if abs(a[0] - b[0]) < 1e-6]
        deltas = [abs(b[1] - a[1]) for (a, b) in paired] if paired else [abs(b[1] - a[1]) for a, b in zip(prev_route, bundle.route)]
        max_step = max(deltas)
        assert max_step < 100, f"Detected wild jump in handle movement: {max_step}"
        # ensure movement direction consistent (increasing Y)
        assert all(b[1] >= a[1] for (a, b) in paired), f"Unexpected direction change in step: prev={prev_route} now={bundle.route}"
        prev_route = list(bundle.route)

    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y() + 20)))
    QTest.qWait(5)

    assert True
