from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE


def test_twistnode_pins_are_orthogonal_and_spaced():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    a = b.source_node
    h = a.get_pin_tip_scene_pos('H')
    l = a.get_pin_tip_scene_pos('L')

    # For source node pins are on LEFT side: x should be equal, y separation should be 3 * GRID_SIZE
    assert round(h.x(), 6) == round(l.x(), 6)
    assert round(abs(h.y() - l.y()), 6) == round(GRID_SIZE * 3, 6)

    # For the target node (right-side) pins should also be orthogonal and spaced
    c = b.target_node
    h2 = c.get_pin_tip_scene_pos('H')
    l2 = c.get_pin_tip_scene_pos('L')
    assert round(h2.x(), 6) == round(l2.x(), 6)
    assert round(abs(h2.y() - l2.y()), 6) == round(GRID_SIZE * 3, 6)
