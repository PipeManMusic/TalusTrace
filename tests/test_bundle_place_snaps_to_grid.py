from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE


def test_bundle_place_snaps_to_grid():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    # Place bundle at coordinates that are NOT aligned to GRID
    b = win.add_twisted_bundle(13, 27, spacing=178)

    a = b.source_node
    c = b.target_node

    # Both nodes' pin tip X positions should be multiples of GRID_SIZE (grid-locked)
    # Check pin *heads* (where pins attach to node) are grid-locked. mapToScene(0,0) for a PinItem
    ah_head = a.pins['H'].mapToScene(0, 0)
    al_head = a.pins['L'].mapToScene(0, 0)
    ch_head = c.pins['H'].mapToScene(0, 0)
    cl_head = c.pins['L'].mapToScene(0, 0)

    print(f"DEBUG: node A pos={a.pos().x(), a.pos().y()}, H_tip={a.get_pin_tip_scene_pos('H').x(), a.get_pin_tip_scene_pos('H').y()}, H_head={ah_head.x(), ah_head.y()}, L_head={al_head.x(), al_head.y()}")
    print(f"DEBUG: node C pos={c.pos().x(), c.pos().y()}, H_tip={c.get_pin_tip_scene_pos('H').x(), c.get_pin_tip_scene_pos('H').y()}, H_head={ch_head.x(), ch_head.y()}, L_head={cl_head.x(), cl_head.y()}")

    def on_grid(v, eps=1e-6):
        return abs(v - round(v / GRID_SIZE) * GRID_SIZE) < eps

    assert on_grid(ah_head.x()) and on_grid(al_head.x())
    assert on_grid(ch_head.x()) and on_grid(cl_head.x())
    # Vertical spacing should be multiples of GRID as well
    assert on_grid(ah_head.y()) and on_grid(al_head.y()) and on_grid(ch_head.y()) and on_grid(cl_head.y())
