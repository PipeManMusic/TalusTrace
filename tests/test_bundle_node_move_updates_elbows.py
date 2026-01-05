import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_midpoint_tracks_node_movement(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)
    a, b = bundle.source_node, bundle.target_node
    old_pos = QPointF(bundle.elbow_pos.x(), bundle.elbow_pos.y())

    # move the source node
    a.setPos(a.pos().x() + 40, a.pos().y() + 10)

    # Elbow position should have moved
    new_pos = QPointF(bundle.elbow_pos.x(), bundle.elbow_pos.y())
    assert not (round(old_pos.x(), 6) == round(new_pos.x(), 6) and round(old_pos.y(), 6) == round(new_pos.y(), 6))


def test_route_translates_with_node(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)
    a, b = bundle.source_node, bundle.target_node

    # add two elbows
    bundle.add_elbow_at(QPointF(80, 0))
    bundle.add_elbow_at(QPointF(120, 0))
    before = list(bundle.route)

    # move node a
    a.setPos(a.pos().x() + 30, a.pos().y() + 5)

    after = list(bundle.route)
    dx = round(after[0][0] - before[0][0], 6)
    dy = round(after[0][1] - before[0][1], 6)
    assert dx == 30 and dy == 5
