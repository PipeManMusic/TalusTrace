import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_handle_follows_elbow_scene_pos(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # Set elbow explicitly
    pos = QPointF(90, 20)
    bundle.set_elbow(pos)

    # After update, there should be an explicit elbow handle that matches elbow_pos
    assert len(bundle.elbow_handles) > 0
    eh = bundle.elbow_handles[0]
    eh_scene = eh.mapToScene(eh.boundingRect().center())
    ep = bundle.elbow_pos
    assert round(eh_scene.x(), 6) == round(ep.x(), 6)
    assert round(eh_scene.y(), 6) == round(ep.y(), 6)


def test_double_click_adds_elbow(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)
    before = len(bundle.route)

    class FakeEvent:
        def __init__(self, pt):
            self._pt = pt
        def scenePos(self):
            return self._pt
        def accept(self):
            pass

    evt = FakeEvent(QPointF(80, 0))
    bundle.mouseDoubleClickEvent(evt)
    assert len(bundle.route) == before + 1
    # Check handle for new elbow exists and is located correctly
    idx = bundle.route.index((80.0, 0.0))
    eh = bundle.elbow_handles[idx]
    eh_scene = eh.mapToScene(eh.boundingRect().center())
    assert round(eh_scene.x(), 6) == 80.0
    assert round(eh_scene.y(), 6) == 0.0
