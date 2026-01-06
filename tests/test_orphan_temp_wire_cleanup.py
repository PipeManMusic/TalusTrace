from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPen
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsLineItem
from talustrace.frontend.app import MainWindow


def test_orphan_temp_wire_cleanup_removes_parentless_lines():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    scene = win.scene

    # Add an orphan line (parentless)
    li = QGraphicsLineItem()
    li.setPen(QPen(Qt.red, 2, Qt.DashLine))
    scene.addItem(li)
    assert li.scene() is scene

    # Call cleanup helper and ensure it's removed
    win.view._cleanup_orphan_temp_wires()
    assert li.scene() is None


def test_cleanup_does_not_remove_child_lines():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    d = win.add_device(0, 0, mark_dirty=False)
    # Create a child line attached to the device (should not be removed)
    child = QGraphicsLineItem(d)
    child.setPen(QPen(Qt.blue, 1))
    d.setPos(100, 100)
    assert child.parentItem() is d
    # Call cleanup
    win.view._cleanup_orphan_temp_wires()
    assert child.scene() is not None
