from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import PIVOT_HIT_RADIUS


def test_pivot_proximity_highlight():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    view = win.view
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    QCoreApplication.processEvents()
    pivot_scene = a.mapToScene(getattr(a, '_pivot', a._rect.center()))
    # call the view helper with a point slightly offset within the radius
    offset = min(4, PIVOT_HIT_RADIUS - 1)
    view.update_pivot_hover_at_scene_pos(QPointF(pivot_scene.x() + offset, pivot_scene.y()))
    assert getattr(a, '_pivot_hover', False) is True
    # Move away
    view.update_pivot_hover_at_scene_pos(QPointF(pivot_scene.x() + PIVOT_HIT_RADIUS + 20, pivot_scene.y()))
    assert getattr(a, '_pivot_hover', False) is False
