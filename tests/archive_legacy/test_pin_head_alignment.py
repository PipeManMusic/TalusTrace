from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE
from talustrace.backend.models import Side


def almost_eq(a, b, eps=1e-6):
    return abs(a - b) < eps


def test_pin_heads_one_grid_from_pivot():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=120)
    a, c = b.source_node, b.target_node

    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    for node in (a, c):
        pivot_scene = node.mapToScene(getattr(node, '_pivot'))
        side = getattr(node, '_bundle_side', None)
        for pid, pin in node.pins.items():
                head = pin.mapToScene(0, 0)
                # Head should be precisely on a intersection
                assert almost_eq(head.x(), round(head.x() / GRID_SIZE) * GRID_SIZE), f"Head x {head.x()} not on vertical grid"
                assert almost_eq(head.y(), round(head.y() / GRID_SIZE) * GRID_SIZE), f"Head y {head.y()} not on horizontal grid"
                if side == Side.LEFT:
                    assert almost_eq(head.x(), pivot_scene.x() + GRID_SIZE), f"Head x {head.x()} not pivot.x+GRID"
                elif side == Side.RIGHT:
                    assert almost_eq(head.x(), pivot_scene.x() - GRID_SIZE), f"Head x {head.x()} not pivot.x-GRID"
                elif side == Side.TOP:
                    assert almost_eq(head.y(), pivot_scene.y() + GRID_SIZE), f"Head y {head.y()} not pivot.y+GRID"
                elif side == Side.BOTTOM:
                    assert almost_eq(head.y(), pivot_scene.y() - GRID_SIZE), f"Head y {head.y()} not pivot.y-GRID"