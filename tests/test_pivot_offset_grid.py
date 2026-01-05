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
    # For source node with target to the right, pivot should be at WIDTH + GRID_SIZE
    expected_x = a.WIDTH + GRID_SIZE
    assert round(pivot_local.x(), 6) == round(expected_x, 6)
    # Vertical center should be at half height
    assert round(pivot_local.y(), 6) == round(a.HEIGHT/2.0, 6)

    # Verify the wire start point is centered between the H and L pin tips
    h_tip = a.get_pin_tip_scene_pos('H')
    l_tip = a.get_pin_tip_scene_pos('L')
    start = b._start_point()
    mid_x = (h_tip.x() + l_tip.x()) / 2
    mid_y = (h_tip.y() + l_tip.y()) / 2
    assert round(start.x(), 6) == round(mid_x, 6)
    assert round(start.y(), 6) == round(mid_y, 6)
