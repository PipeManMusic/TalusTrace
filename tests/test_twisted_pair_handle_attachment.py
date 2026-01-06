import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_elbow_handles_follow_route_on_node_move(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # add two elbows
    bundle.add_elbow_at(QPointF(80, 0))
    bundle.add_elbow_at(QPointF(120, 0))
    idx = bundle.route.index((80.0, 0.0))

    # get initial positions
    eh = bundle.elbow_handles[idx]
    eh_scene_before = eh.mapToScene(eh.boundingRect().center())
    route_before = list(bundle.route)

    # move source node (note: node positions snap to GRID_SIZE)
    a = bundle.source_node
    old_node_snapped = QPointF(round(a.pos().x() / 20) * 20, round(a.pos().y() / 20) * 20)
    a.setPos(a.pos().x() + 30, a.pos().y() + 5)

    # route should translate accordingly (respecting grid snap)
    route_after = list(bundle.route)
    new_node_snapped = QPointF(round(a.pos().x() / 20) * 20, round(a.pos().y() / 20) * 20)
    expected_dx = new_node_snapped.x() - old_node_snapped.x()
    expected_dy = new_node_snapped.y() - old_node_snapped.y()
    assert route_after[0][0] - route_before[0][0] == expected_dx
    assert route_after[0][1] - route_before[0][1] == expected_dy

    # handle scene pos should now match new route pos
    eh_scene_after = eh.mapToScene(eh.boundingRect().center())
    rx, ry = route_after[idx]
    assert round(eh_scene_after.x(), 6) == round(rx, 6)
    assert round(eh_scene_after.y(), 6) == round(ry, 6)
