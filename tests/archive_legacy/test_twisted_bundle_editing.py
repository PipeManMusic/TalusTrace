import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import QPointF
from talustrace.frontend.items import TwistedBundleItem, TwistNodeItem

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_add_move_delete_elbows(qapp):
    node_a = TwistNodeItem(on_changed=None)
    node_b = TwistNodeItem(on_changed=None)
    bundle = TwistedBundleItem(node_a, node_b, on_changed=None)

    # Add two elbows
    bundle.add_elbow_at(QPointF(80, 0))
    bundle.add_elbow_at(QPointF(160, 0))
    assert len(bundle.route) == 2

    # Move first elbow
    bundle.move_elbow(0, QPointF(80, 20))
    assert bundle.route[0] == (80.0, 20.0)

    # Delete first elbow
    bundle.delete_elbow(0)
    assert len(bundle.route) == 1

    # Delete remaining
    bundle.delete_elbow(0)
    assert len(bundle.route) == 0
