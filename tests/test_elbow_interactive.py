import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QPoint, Qt
from PySide6.QtTest import QTest
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_elbow_interactive_drag(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # Add an elbow
    bundle.add_elbow_at(QPointF(80, 0))
    idx = bundle.route.index((80.0, 0.0))
    eh = bundle.elbow_handles[idx]

    # Map handle center to view coords
    ep_scene = eh.mapToScene(eh.boundingRect().center())
    view_pos = win.view.mapFromScene(ep_scene)

    old_route = list(bundle.route)

    # Simulate press, small move and release
    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, view_pos)
    QTest.qWait(10)
    # Move by +20 pixels in view coords
    moved_view_pos = QPoint(int(view_pos.x()), int(view_pos.y() + 20))
    QTest.mouseMove(win.view.viewport(), moved_view_pos)
    QTest.qWait(10)
    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, moved_view_pos)

    assert bundle.route != old_route, f"route didn't change after interactive elbow move; old={old_route} new={bundle.route}"
    newy = bundle.route[idx][1]
    assert newy > 5 and newy <= 200, f"elbow didn't move as expected, y={newy}"
