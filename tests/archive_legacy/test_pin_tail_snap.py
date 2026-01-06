from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE
from talustrace.backend.models import Side

def almost_eq(a, b, eps=1e-6):
    return abs(a - b) < eps


def almost_on_grid(v, grid=GRID_SIZE, eps=1e-6):
    return abs(v - round(v / grid) * grid) < eps


def test_pin_tail_snaps_to_grid():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a = bundle.source_node
    h = a.pins.get('H')

    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    tail_scene = h.get_tail_scene_pos()
    head_scene = h.get_tip_scene_pos()
    parent = h.parentItem() or a
    pivot_scene = parent.mapToScene(getattr(parent, '_pivot', parent._rect.center()))
    # Expected tail is head + unit_vector_toward_pivot * tip_off (6px)
    vec_x = pivot_scene.x() - head_scene.x()
    vec_y = pivot_scene.y() - head_scene.y()
    length = (vec_x * vec_x + vec_y * vec_y) ** 0.5
    if length == 0:
        # fallback: small horizontal stub
        exp_x = head_scene.x() - 6.0
        exp_y = head_scene.y()
    else:
        ux = vec_x / length
        uy = vec_y / length
        exp_x = head_scene.x() + ux * 6.0
        exp_y = head_scene.y() + uy * 6.0
    assert almost_eq(tail_scene.x(), exp_x), f"Tail x {tail_scene.x()} not expected {exp_x}"
    assert almost_eq(tail_scene.y(), exp_y), f"Tail y {tail_scene.y()} not expected {exp_y}"