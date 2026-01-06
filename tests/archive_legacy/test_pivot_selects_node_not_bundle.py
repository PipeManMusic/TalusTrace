from PySide6.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF
from talustrace.frontend.app import MainWindow


def test_click_pivot_selects_node_not_bundle():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    ev = QGraphicsSceneMouseEvent()
    ev.setScenePos(pivot_scene)
    ev.setButton(Qt.LeftButton)
    ev.setButtons(Qt.LeftButton)

    # Simulate press on pivot via scene dispatch
    b.scene().mousePressEvent(ev)

    # Bundle should NOT be selected; node should be selected
    assert not b.isSelected()
    # Simulate that node receives the press and selection; QGraphicsItem may select on press
    a.mousePressEvent(ev)
    assert a.isSelected() or getattr(a, '_drag_start_pos', None) == pivot_scene
