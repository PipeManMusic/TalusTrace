from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import SELECTED_COLOR


def test_bundle_selection_highlights_node_with_outline_not_fill():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    src = b.source_node
    tgt = b.target_node

    # select the bundle
    b.setSelected(True)
    QCoreApplication.processEvents()

    # The nodes should show an outline (pen) of SELECTED_COLOR, but pivot brush must be NoBrush (no fill)
    from PySide6.QtCore import Qt
    try:
        src_brush_style = src.control_pivot.brush().style()
    except Exception:
        src_brush_style = None
    assert src_brush_style == Qt.NoBrush
    assert src.control_pivot.pen().color() == SELECTED_COLOR

    try:
        tgt_brush_style = tgt.control_pivot.brush().style()
    except Exception:
        tgt_brush_style = None
    assert tgt_brush_style == Qt.NoBrush
    assert tgt.control_pivot.pen().color() == SELECTED_COLOR

    # Deselect bundle - nodes should no longer have selected pen color
    b.setSelected(False)
    QCoreApplication.processEvents()
    assert src.control_pivot.pen().color() != SELECTED_COLOR
    assert tgt.control_pivot.pen().color() != SELECTED_COLOR
