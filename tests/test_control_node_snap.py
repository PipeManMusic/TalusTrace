from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE


def test_control_node_snaps_on_move():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=120)
    a = b.source_node

    # Move node to a non-grid position
    a.setPos(13, 37)
    # Process events so itemChange is applied
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    snapped = QPointF(round(13 / GRID_SIZE) * GRID_SIZE, round(37 / GRID_SIZE) * GRID_SIZE)
    assert a.pos() == snapped, f"Expected node to snap to {snapped}, got {a.pos()}"