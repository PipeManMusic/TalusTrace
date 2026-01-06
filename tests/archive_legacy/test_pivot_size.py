from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import CONTROL_PIVOT_DIAM, CONTROL_DOT_DIAM, PIVOT_COLOR, TwistNodeItem


def test_control_pivot_and_dot_size():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    # Check pivot diameter and dot diameter
    pivot_rect = a.control_pivot.rect()
    dot_rect = a.control_dot.rect()
    assert pivot_rect.width() == CONTROL_PIVOT_DIAM
    assert pivot_rect.height() == CONTROL_PIVOT_DIAM
    assert dot_rect.width() == CONTROL_DOT_DIAM
    assert dot_rect.height() == CONTROL_DOT_DIAM

    # Ensure a free node (not attached to a bundle) shows a filled blue pivot
    n = TwistNodeItem()
    win.scene.addItem(n)
    try:
        brush_color = n.control_pivot.brush().color()
    except Exception:
        brush_color = None
    assert brush_color == PIVOT_COLOR