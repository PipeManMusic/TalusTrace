import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import TwistNodeItem
from PySide6.QtCore import QPointF
from talustrace.backend.models import Side

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_pivot_outside_node_and_highlight(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a = bundle.source_node

    pivot_scene = a.mapToScene(a._pivot)
    # pivot should lie outside node scene bounding rect
    bbox = a.sceneBoundingRect()
    assert not bbox.contains(pivot_scene)

    # selecting the bundle should highlight the node pivot
    bundle.setSelected(True)
    assert getattr(a, '_pivot_highlight', False) is True
    bundle.setSelected(False)
    assert getattr(a, '_pivot_highlight', False) is False


def test_rotate_never_points_hl_at_bundle(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)
    a, b = bundle.source_node, bundle.target_node

    # Ensure a has a bundle side set
    assert getattr(a, '_bundle_side', None) is not None

    # Remember initial H side
    initial_h = a.pins['H'].model.side

    # Try rotating multiple times and ensure H side never equals bundle side
    for _ in range(8):
        a.rotate_cw()
        h_side = a.pins['H'].model.side
        assert h_side != getattr(a, '_bundle_side', None)
