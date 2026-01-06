from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from talustrace.frontend.device_minimal import DeviceItem
from talustrace.frontend.items_baseline import GRID_SIZE


def test_device_pins_snap_to_grid_and_spacing():
    app = QApplication.instance() or QApplication([])
    scene_parent = None

    # Create a device placed at non-grid coords and ensure it snaps when added
    d = DeviceItem(13, 27)

    # pin head scene positions should be multiples of GRID_SIZE
    h_scene = d.get_pin_tip_scene_pos('H')
    l_scene = d.get_pin_tip_scene_pos('L')
    assert h_scene is not None and l_scene is not None

    assert round(h_scene.x() / GRID_SIZE, 6) == round(h_scene.x() // GRID_SIZE, 6) or (h_scene.x() % GRID_SIZE == 0)
    assert round(h_scene.y() / GRID_SIZE, 6) == round(h_scene.y() // GRID_SIZE, 6) or (h_scene.y() % GRID_SIZE == 0)
    assert round(l_scene.x() / GRID_SIZE, 6) == round(l_scene.x() // GRID_SIZE, 6) or (l_scene.x() % GRID_SIZE == 0)
    assert round(l_scene.y() / GRID_SIZE, 6) == round(l_scene.y() // GRID_SIZE, 6) or (l_scene.y() % GRID_SIZE == 0)

    # vertical spacing between H and L should be 2 * GRID_SIZE
    spacing = abs(l_scene.y() - h_scene.y())
    assert round(spacing, 6) == round(GRID_SIZE * 2, 6)
