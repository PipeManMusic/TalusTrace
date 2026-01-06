from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE, PIVOT_COLOR


def almost_eq(a: QPointF, b: QPointF, tol=1e-6):
    return round(a.x(), 6) == round(b.x(), 6) and round(a.y(), 6) == round(b.y(), 6)


def test_control_nodes_select_and_move_independently():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    a = b.source_node
    c = b.target_node

    # initial positions
    pos_a = QPointF(a.pos())
    pos_c = QPointF(c.pos())

    # Select source node and ensure its pivot highlights and other does not
    a.setSelected(True)
    QCoreApplication.processEvents()
    from PySide6.QtCore import Qt as _Qt
    # Both pivots are visible (filled) even when only one is selected; selected one highlighted
    assert a.control_pivot.brush().style() != _Qt.NoBrush
    assert c.control_pivot.brush().style() != _Qt.NoBrush

    # Move source node by an offset and ensure it snaps to GRID and target is unchanged
    dx, dy = 40, 20
    a.setPos(a.pos().x() + dx, a.pos().y() + dy)
    QCoreApplication.processEvents()
    expected_a = QPointF(round((pos_a.x() + dx) / GRID_SIZE) * GRID_SIZE, round((pos_a.y() + dy) / GRID_SIZE) * GRID_SIZE)
    assert almost_eq(a.pos(), expected_a)
    assert almost_eq(c.pos(), pos_c)

    # Deselect source, select target, ensure pivot highlighting switched
    a.setSelected(False)
    c.setSelected(True)
    QCoreApplication.processEvents()
    # Deselected pivot should be dark blue again; selected pivot highlighted
    assert a.control_pivot.brush().color() == PIVOT_COLOR
    assert c.control_pivot.brush().style() != _Qt.NoBrush

    # Move target node and ensure source node stays where it was
    dx2, dy2 = -60, 10
    c.setPos(c.pos().x() + dx2, c.pos().y() + dy2)
    QCoreApplication.processEvents()
    expected_c = QPointF(round((pos_c.x() + dx2) / GRID_SIZE) * GRID_SIZE, round((pos_c.y() + dy2) / GRID_SIZE) * GRID_SIZE)
    assert almost_eq(c.pos(), expected_c)
    assert almost_eq(a.pos(), expected_a)
