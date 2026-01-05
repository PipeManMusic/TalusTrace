from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import SELECTED_COLOR, GRID_SIZE


def test_bundle_endpoints_exist_and_highlight():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    # The endpoint markers should exist and be non-movable
    assert getattr(b, 'start_marker', None) is not None
    assert getattr(b, 'end_marker', None) is not None

    # Markers should be near the start/end points
    s = b._start_point()
    e = b._end_point()
    sm_scene = b.start_marker.mapToScene(b.start_marker.boundingRect().center())
    em_scene = b.end_marker.mapToScene(b.end_marker.boundingRect().center())
    # within a small tolerance (GRID_SIZE/2)
    assert abs(sm_scene.x() - s.x()) <= GRID_SIZE/2
    assert abs(sm_scene.y() - s.y()) <= GRID_SIZE/2
    assert abs(em_scene.x() - e.x()) <= GRID_SIZE/2
    assert abs(em_scene.y() - e.y()) <= GRID_SIZE/2

    # Selecting the bundle should change marker outline (pen) to SELECTED_COLOR
    b.setSelected(True)
    # QGraphics selection dispatches itemChange synchronously; check pen colors
    assert b.start_marker.pen().color() == SELECTED_COLOR
    assert b.end_marker.pen().color() == SELECTED_COLOR

    # Deselect should restore default gray pen color
    b.setSelected(False)
    assert b.start_marker.pen().color() != SELECTED_COLOR
    assert b.end_marker.pen().color() != SELECTED_COLOR

    # Markers use hollow brush (outline) to avoid competing with pin tips
    assert b.start_marker.brush().style() == 0 or b.start_marker.brush().style() == getattr(__import__('PySide6.QtCore', fromlist=['Qt']).Qt, 'NoBrush')
    assert b.end_marker.brush().style() == 0 or b.end_marker.brush().style() == getattr(__import__('PySide6.QtCore', fromlist=['Qt']).Qt, 'NoBrush')
