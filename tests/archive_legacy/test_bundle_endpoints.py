from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import SELECTED_COLOR, GRID_SIZE


def test_bundle_endpoints_exist_and_highlight():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    # Control pivot on the source and target nodes should exist and be positioned at the bundle connection point
    assert getattr(b.source_node, 'control_pivot', None) is not None
    assert getattr(b.target_node, 'control_pivot', None) is not None

    # Control pivot should be near the start/end points
    s = b._start_point()
    e = b._end_point()
    sm_scene = b.source_node.control_pivot.mapToScene(b.source_node.control_pivot.boundingRect().center())
    em_scene = b.target_node.control_pivot.mapToScene(b.target_node.control_pivot.boundingRect().center())
    # within a small tolerance (GRID_SIZE/2)
    assert abs(sm_scene.x() - s.x()) <= GRID_SIZE/2
    assert abs(sm_scene.y() - s.y()) <= GRID_SIZE/2
    assert abs(em_scene.x() - e.x()) <= GRID_SIZE/2
    assert abs(em_scene.y() - e.y()) <= GRID_SIZE/2

    # Selecting the bundle should highlight the control pivots
    b.setSelected(True)
    # QGraphics selection dispatches itemChange synchronously; check control pivot brush color
    assert b.source_node.control_pivot.brush().style() != 0
    assert b.target_node.control_pivot.brush().style() != 0

    # Deselect should restore hollow brush (outline)
    b.setSelected(False)
    from PySide6.QtCore import Qt as _Qt
    assert b.source_node.control_pivot.brush().style() == _Qt.NoBrush
    assert b.target_node.control_pivot.brush().style() == _Qt.NoBrush

    # Existing bundle markers (if present) should remain hollow to avoid competing with pin tips
    from PySide6.QtCore import Qt as _Qt
    if getattr(b, 'start_marker', None):
        assert b.start_marker.brush().style() == _Qt.NoBrush
    if getattr(b, 'end_marker', None):
        assert b.end_marker.brush().style() == _Qt.NoBrush
