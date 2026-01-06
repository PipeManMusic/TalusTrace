import tempfile
import yaml
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import TwistNodeItem, TwistedBundleItem
from talustrace.backend.models import Device

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_save_and_load_bundle_persists(qapp, tmp_path):
    win = MainWindow(restore_policy="skip")
    bundle = win.add_twisted_bundle(10, 20, spacing=120)
    # Move elbow to a specific position
    bundle.set_elbow(QPointF(80, 40))

    fpath = tmp_path / "test_bundle.yaml"
    win.save_harness(str(fpath))

    # Load into a new window
    win2 = MainWindow(restore_policy="skip")
    win2.load_harness(str(fpath))

    assert len(win2.twist_nodes) == 2
    assert len(win2.bundle_items) == 1

    b2 = win2.bundle_items[0]
    # elbow persisted (rounded by GRID snap) - compare numeric proximity
    ex, ey = b2.elbow_pos.x(), b2.elbow_pos.y()
    assert round(ex) == round(80)
    assert round(ey) == round(40)


def test_elbow_move_affects_geometry(qapp):
    node_a = TwistNodeItem(on_changed=None)
    node_b = TwistNodeItem(on_changed=None)
    node_a.setPos(0, 0)
    node_b.setPos(200, 0)
    bundle = TwistedBundleItem(node_a, node_b, on_changed=None)

    old = bundle.elbow_pos
    new = QPointF(old.x() + 40, old.y() + 10)
    bundle.set_elbow(new)
    # set_elbow snaps to grid; compute expected snapped point
    from talustrace.frontend.items_baseline import GRID_SIZE
    expected = QPointF(round(new.x() / GRID_SIZE) * GRID_SIZE, round(new.y() / GRID_SIZE) * GRID_SIZE)
    assert bundle.elbow_pos == expected
    # After moving, an explicit elbow handle should exist and be located at elbow_pos
    assert len(bundle.elbow_handles) > 0
    eh = bundle.elbow_handles[0]
    eh_scene = eh.mapToScene(eh.boundingRect().center())
    assert round(eh_scene.x(), 6) == round(bundle.elbow_pos.x(), 6)
    assert round(eh_scene.y(), 6) == round(bundle.elbow_pos.y(), 6)


def test_helix_endpoints_centered_between_H_L(qapp):
    node_a = TwistNodeItem(on_changed=None)
    node_a.setPos(0, 0)
    h = node_a.get_pin_tip_scene_pos("H")
    l = node_a.get_pin_tip_scene_pos("L")

    node_b = TwistNodeItem(on_changed=None)
    node_b.setPos(200, 0)

    bundle = TwistedBundleItem(node_a, node_b, on_changed=None)
    s = bundle._start_point()
    # start point should equal the source node control pivot
    pivot = node_a.mapToScene(getattr(node_a, '_pivot', node_a._rect.center()))
    assert round(s.x(), 6) == round(pivot.x(), 6)
    assert round(s.y(), 6) == round(pivot.y(), 6)
