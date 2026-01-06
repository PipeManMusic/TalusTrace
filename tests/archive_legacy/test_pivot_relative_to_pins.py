from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE
from talustrace.backend.models import Side


def test_pivot_one_grid_from_pins():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    a = b.source_node
    h = a.get_pin_tip_scene_pos('H')
    l = a.get_pin_tip_scene_pos('L')
    # Force recalculation to ensure pivot honors updated logic
    print(f"DEBUG: node_type={type(a)}, has_update_method={hasattr(a,'_update_pivot_from_pins')}")
    try:
        a._update_pivot_from_pins()
    except Exception:
        pass
    pivot_scene = a.mapToScene(a._pivot)

    # Pivot should sit one GRID unit away from the pin head line on the bundle side.
    # Debug: inspect coordinates
    side = getattr(a, '_bundle_side', None) or Side.LEFT
    print(f"DEBUG: node_pos={a.pos().x(), a.pos().y()}, H={h.x(), h.y()}, L={l.x(), l.y()}, pivot_local={a._pivot.x(), a._pivot.y()}, pivot_scene={pivot_scene.x(), pivot_scene.y()}, bundle_side={side}")
    if side == Side.LEFT:
        expected_x = round(min(h.x(), l.x()) - GRID_SIZE, 6)
    elif side == Side.RIGHT:
        expected_x = round(max(h.x(), l.x()) + GRID_SIZE, 6)
    elif side == Side.TOP:
        expected_x = round(((h.x() + l.x()) / 2.0) / GRID_SIZE) * GRID_SIZE
    else:  # BOTTOM
        expected_x = round(((h.x() + l.x()) / 2.0) / GRID_SIZE) * GRID_SIZE
    assert round(pivot_scene.x(), 6) == round(expected_x, 6)
    # pivot y should be the midpoint between pins (snapped to grid) unless top/bottom
    if side in (Side.LEFT, Side.RIGHT):
        # Pivot Y should sit between the H/L pin heads (snapped to GRID)
        expected_y = round(((h.y() + l.y()) / 2.0) / GRID_SIZE) * GRID_SIZE
    elif side == Side.TOP:
        expected_y = round((min(h.y(), l.y()) - GRID_SIZE) / GRID_SIZE) * GRID_SIZE
    else:
        expected_y = round((max(h.y(), l.y()) + GRID_SIZE) / GRID_SIZE) * GRID_SIZE
    assert round(pivot_scene.y(), 6) == round(expected_y, 6)
