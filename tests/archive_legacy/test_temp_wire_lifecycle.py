from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import Qt
from talustrace.frontend.app import MainWindow


def test_start_wiring_then_new_file_cleans_temp_wire():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    # start a wiring operation
    pin = win.add_device(0, 0, mark_dirty=False).pins.get('H')
    # Use view API to start wiring
    win.view.start_wiring(pin)
    # temp_wire should be present
    found_temp = any(isinstance(it, QGraphicsLineItem) and it.parentItem() is None for it in win.scene.items())
    assert found_temp
    # Now create a new file which should clear scene and cleanup orphans
    win.new_file()
    found_temp_after = any(isinstance(it, QGraphicsLineItem) and it.parentItem() is None for it in win.scene.items())
    assert not found_temp_after

def test_temp_wire_tagging_and_cleanup():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    pin = win.add_device(0, 0, mark_dirty=False).pins.get('H')
    win.view.start_wiring(pin)
    # temp_wire should be data-tagged
    tagged = any(getattr(it, 'data', lambda i: None)(0) == 'temp_wire' for it in win.scene.items() if isinstance(it, QGraphicsLineItem))
    assert tagged
    # cleanup explicitly
    win.view._cleanup_orphan_temp_wires()
    assert not any(isinstance(it, QGraphicsLineItem) and it.parentItem() is None for it in win.scene.items())
