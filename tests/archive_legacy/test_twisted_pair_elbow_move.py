import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_elbow_handle_mouse_move(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # Add elbow
    bundle.add_elbow_at(QPointF(80, 0))
    idx = bundle.route.index((80.0, 0.0))
    eh = bundle.elbow_handles[idx]

    class FakeMove:
        def __init__(self, pt):
            self._pt = pt
        def scenePos(self):
            return self._pt
        def accept(self):
            pass

    # Move the elbow by +20 in Y
    old_route = list(bundle.route)
    ep_scene = eh.mapToScene(eh.boundingRect().center())
    moved = QPointF(ep_scene.x(), ep_scene.y() + 20)
    evt = FakeMove(moved)
    eh.mouseMoveEvent(evt)

    assert bundle.route != old_route, f"route didn't change after elbow mouse move; old={old_route} new={bundle.route}"
    # Check the moved elbow's Y increased
    newy = bundle.route[idx][1]
    assert newy > 5 and newy <= 40, f"elbow didn't move as expected, y={newy}"
