from PySide6.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import PIVOT_HIT_RADIUS


def test_click_slightly_off_pivot_still_anchors_to_pivot():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    # Click slightly off pivot but within PIVOT_HIT_RADIUS
    offset = min(6, PIVOT_HIT_RADIUS - 1)
    click_point = QPointF(pivot_scene.x() + offset, pivot_scene.y())

    ev = QGraphicsSceneMouseEvent()
    ev.setScenePos(click_point)
    ev.setButton(Qt.LeftButton)
    ev.setButtons(Qt.LeftButton)

    # Dispatch to node directly as in scene routing
    a.mousePressEvent(ev)
    assert a._drag_start_pos == pivot_scene
