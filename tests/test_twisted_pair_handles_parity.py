import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_segment_handles_and_doubleclick(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # Initially a single segment (start->end)
    assert len(bundle.segment_handles) == 1

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
    # After adding an elbow we should have one additional segment handle
    assert len(bundle.segment_handles) == 2


def test_segment_handle_move_updates_route(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # Add an elbow at (80, 0)
    bundle.add_elbow_at(QPointF(80, 0))
    assert (80.0, 0.0) in bundle.route
    idx = bundle.route.index((80.0, 0.0))

    # Choose the segment handle left of the new elbow (segment 0)
    seg_handle = bundle.segment_handles[0]

    # Simulate dragging the segment mid by +20 in Y
    class FakeMove:
        def __init__(self, pt):
            self._pt = pt
        def scenePos(self):
            return self._pt
        def accept(self):
            pass

    # Compute a new mid point (relative to scene)
    mid_scene = seg_handle.mapToScene(seg_handle.boundingRect().center())
    moved = QPointF(mid_scene.x(), mid_scene.y() + 20)
    evt = FakeMove(moved)

    old_route = list(bundle.route)
    seg_handle.mouseMoveEvent(evt)

    # Ensure the route changed in response to segment move
    assert bundle.route != old_route, f"route did not change after moving segment handle; old={old_route} new={bundle.route}"
    # At least one route Y value should have increased by a positive amount
    deltas = [y - oy for ((ox, oy), (x, y)) in zip(old_route, bundle.route)] if len(old_route) == len(bundle.route) else [y for (x, y) in bundle.route]
    assert any(d > 0 for d in deltas), f"expected some route points to increase in Y; deltas={deltas}"
