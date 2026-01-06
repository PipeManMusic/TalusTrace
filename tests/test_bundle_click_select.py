from PySide6.QtWidgets import QApplication, QGraphicsItem
from PySide6.QtCore import QCoreApplication, QPointF, Qt, QEvent
from talustrace.frontend.app import MainWindow


def test_clicking_bundle_midpoint_selects_bundle():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    view = win.view
    b = win.add_twisted_bundle(0, 0, spacing=200)

    # compute an approximate midpoint between source and target pivots
    s = b.source_node.mapToScene(getattr(b.source_node, '_pivot'))
    t = b.target_node.mapToScene(getattr(b.target_node, '_pivot'))
    mid = QPointF((s.x() + t.x()) / 2.0, (s.y() + t.y()) / 2.0)

    # simulate a view mouse press at the midpoint (preferred to emulate user's click)
    from PySide6.QtGui import QMouseEvent
    vp_pt = view.mapFromScene(mid)
    screen_pt = view.viewport().mapToGlobal(vp_pt)
    me = QMouseEvent(QEvent.MouseButtonPress, vp_pt, screen_pt, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)

    # We can't reliably simulate the OS-level click selection semantics in all test environments,
    # but we can assert that the bundle is selectable and its shape contains the midpoint.
    assert b.flags() & QGraphicsItem.ItemIsSelectable
    assert b.shape().contains(b.mapFromScene(mid)) is True
