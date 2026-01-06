from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import TwistNodeItem, GRID_SIZE
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF


def test_bundle_group_origin_aligns_with_left_pivot():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    g = win._build_bundle_group(spacing=200)
    # The group should contain two children (nodes) whose positions are shifted so
    # that the left node's _pivot is at the group's origin (0,0).
    children = [c for c in g.childItems()]
    # Find a TwistNodeItem among children
    nodes = [c for c in children if isinstance(c, TwistNodeItem)]
    assert len(nodes) >= 1
    a = nodes[0]
    pivot = getattr(a, '_pivot', None)
    assert pivot is not None
    # Node position should be equal to -pivot so the pivot maps to group origin
    assert QPointF(a.pos().x(), a.pos().y()) == QPointF(-pivot.x(), -pivot.y())
    # The other node should be shifted relative to the pivot by approximately spacing
    others = [n for n in nodes if n is not a]
    if others:
        b = others[0]
        delta = b.pos() - a.pos()
        # x delta should be approximately spacing (200) modulo grid snaps
        assert abs(delta.x() - 200) <= GRID_SIZE
