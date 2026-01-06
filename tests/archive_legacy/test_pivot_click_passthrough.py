from PySide6.QtWidgets import QApplication, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt
from talustrace.frontend.app import MainWindow


def test_pivot_children_do_not_consume_mouse_events():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    # Children should be non-interactive (NoButton)
    assert a.control_pivot.acceptedMouseButtons() == Qt.NoButton
    assert a.control_dot.acceptedMouseButtons() == Qt.NoButton

    # Clicking the pivot coordinates should result in the scene delivering the press to the node
    pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    ev = QGraphicsSceneMouseEvent()
    ev.setScenePos(pivot_scene)
    ev.setButton(Qt.LeftButton)
    ev.setButtons(Qt.LeftButton)

    # The node should be present in the item stack at that scene coordinate
    items = b.scene().items(pivot_scene)
    assert any(it is a or getattr(it, 'parentItem', lambda: None)() is a for it in items), f"Node not found in scene items at pivot: {items}"

    # Dispatch the scene press and assert the node gets selected/anchored and bundle does not
    b.scene().mousePressEvent(ev)
    # Event should be accepted by the scene routing so the view doesn't start a rubber-band drag
    assert ev.isAccepted()
    assert a.isSelected() or getattr(a, '_drag_start_pos', None) == pivot_scene
    assert not b.isSelected()

    # Ensure selecting the node does not highlight the other node's pivot
    from PySide6.QtCore import Qt as _Qt
    assert a.control_pivot.brush().style() != _Qt.NoBrush
    # Other node remains un-highlighted (not filled with SELECTED_COLOR)
    from talustrace.frontend.items_baseline import PIVOT_COLOR
    assert b.target_node.control_pivot.brush().color() == PIVOT_COLOR
