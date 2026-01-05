import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import TwistNodeItem
from PySide6.QtCore import QPointF

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_pivot_offset_and_tip_grip(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a, b = bundle.source_node, bundle.target_node

    # pivot should be offset toward the open pins (opposite the bundle side)
    center = a._rect.center()
    pivot = getattr(a, '_pivot', None)
    assert pivot is not None
    # The pivot is placed outward on the bundle side to avoid interfering with pin clicks;
    # confirm it is NOT too close to the tips (i.e. it is offset outward) and also not absurdly far.
    h = a.pins.get('H')
    assert h is not None
    pivot_scene = a.mapToScene(pivot)
    l = a.pins.get('L')
    h_tip_scene = h.get_tip_scene_pos()
    l_tip_scene = l.get_tip_scene_pos() if l else h_tip_scene
    dist_h = ((pivot_scene.x() - h_tip_scene.x())**2 + (pivot_scene.y() - h_tip_scene.y())**2)**0.5
    dist_l = ((pivot_scene.x() - l_tip_scene.x())**2 + (pivot_scene.y() - l_tip_scene.y())**2)**0.5
    dist = min(dist_h, dist_l)
    assert dist > 12, f"Pivot unexpectedly close to H/L tip: {dist}"
    assert dist < 200, f"Pivot unexpectedly far from H/L tip: {dist}"

    # Tip should be small and subtle (6x6)
    tip = h.tip
    br = tip.boundingRect()
    assert br.width() >= 6 and br.height() >= 6
