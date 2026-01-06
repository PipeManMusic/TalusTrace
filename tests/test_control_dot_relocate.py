from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QPointF, Qt
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from talustrace.frontend.app import MainWindow


def test_clicking_control_dot_moves_pivot_without_modifier():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    view = win.view
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    QCoreApplication.processEvents()
    pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))

    # Simulate a scene-level press on the control dot (the scene routing will mark _last_child_pressed)
    ev_press = QGraphicsSceneMouseEvent()
    ev_press.setScenePos(pivot_scene)
    ev_press.setButton(Qt.LeftButton)
    ev_press.setButtons(Qt.LeftButton)

    win.scene.mousePressEvent(ev_press)

    # Simulate move without modifiers
    ev_move = QGraphicsSceneMouseEvent()
    ev_move.setScenePos(QPointF(pivot_scene.x() + 40, pivot_scene.y()))
    ev_move.setButtons(Qt.LeftButton)

    # Directly call mouseMoveEvent on the node (as the node should be in pivot-dragging state)
    a.mouseMoveEvent(ev_move)

    new_pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    assert new_pivot_scene.x() >= pivot_scene.x() + 20

    # Release
    ev_rel = QGraphicsSceneMouseEvent()
    ev_rel.setScenePos(QPointF(pivot_scene.x() + 40, pivot_scene.y()))
    ev_rel.setButton(Qt.LeftButton)
    ev_rel.setButtons(Qt.NoButton)

    win.scene.mouseReleaseEvent(ev_rel)

    final = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    assert final.x() == new_pivot_scene.x()