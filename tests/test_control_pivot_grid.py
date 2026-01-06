from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE


def almost_on_grid(v, grid=GRID_SIZE, eps=1e-6):
    return abs(v - round(v / grid) * grid) < eps


def test_control_pivot_is_on_grid():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(7, 13, spacing=120)
    a = b.source_node

    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    pivot_scene = a.mapToScene(getattr(a, '_pivot'))
    assert almost_on_grid(pivot_scene.x()), f"Pivot x {pivot_scene.x()} not aligned to grid"
    assert almost_on_grid(pivot_scene.y()), f"Pivot y {pivot_scene.y()} not aligned to grid"