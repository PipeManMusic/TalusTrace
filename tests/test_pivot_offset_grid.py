from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE


def test_pivot_offset_matches_grid():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    a = b.source_node
    # Pivot stored in node local coords
    pivot_local = getattr(a, '_pivot')
    # Pivot scene position should be snapped to GRID: compute expected scene coords
    expected_scene_x = round((a.WIDTH + GRID_SIZE) / GRID_SIZE) * GRID_SIZE
    expected_scene_y = round((a.HEIGHT / 2.0) / GRID_SIZE) * GRID_SIZE
    pivot_scene = a.mapToScene(getattr(a, '_pivot'))
    assert round(pivot_scene.x(), 6) == round(expected_scene_x, 6)
    assert round(pivot_scene.y(), 6) == round(expected_scene_y, 6)

    # Verify the wire start point connects to the node control pivot center
    start = b._start_point()
    assert round(start.x(), 6) == round(pivot_scene.x(), 6)
    assert round(start.y(), 6) == round(pivot_scene.y(), 6)
