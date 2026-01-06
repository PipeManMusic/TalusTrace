from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from talustrace.frontend.app import MainWindow


def test_shift_drag_relocates_pivot():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    QCoreApplication.processEvents()
    pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))

    # Press on the pivot with Shift modifier
    ev_press = QGraphicsSceneMouseEvent()
    ev_press.setScenePos(pivot_scene)
    ev_press.setButton(Qt.LeftButton)
    ev_press.setButtons(Qt.LeftButton)
    ev_press.setModifiers(Qt.ShiftModifier)

    a.mousePressEvent(ev_press)

    # Move pivot 40 units to the right while holding button
    ev_move = QGraphicsSceneMouseEvent()
    ev_move.setScenePos(QPointF(pivot_scene.x() + 40, pivot_scene.y()))
    ev_move.setButtons(Qt.LeftButton)

    a.mouseMoveEvent(ev_move)

    new_pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    # Should have moved right by at least one GRID step
    assert new_pivot_scene.x() >= pivot_scene.x() + 20
    # Pivot should be locked after relocation
    assert getattr(a, '_pivot_locked', False) is True

    # Release ends pivot dragging
    ev_rel = QGraphicsSceneMouseEvent()
    ev_rel.setScenePos(QPointF(pivot_scene.x() + 40, pivot_scene.y()))
    ev_rel.setButton(Qt.LeftButton)
    ev_rel.setButtons(Qt.NoButton)
    ev_rel.setModifiers(Qt.NoModifier)
    a.mouseReleaseEvent(ev_rel)

    # Ensure value persisted
    final_pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    assert final_pivot_scene.x() == new_pivot_scene.x()
