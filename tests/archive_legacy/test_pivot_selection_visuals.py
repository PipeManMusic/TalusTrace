from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import (
    TwistNodeItem,
    CONTROL_PIVOT_DIAM,
    SELECTED_COLOR,
)


def test_selection_indicator_shows_for_bundled_node():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    # Node should be bundled
    assert getattr(a, 'bundle_refs', None)

    # Select and verify ring + label are visible and pivot is colored
    a.setSelected(True)
    QCoreApplication.processEvents()

    assert getattr(a, 'control_pivot_ring', None) is not None
    assert a.control_pivot_ring.isVisible() is True
    assert getattr(a, 'control_pivot_label', None) is not None
    assert a.control_pivot_label.isVisible() is True
    assert a.control_pivot.brush().color() == SELECTED_COLOR

    # Deselect and ensure visuals are hidden
    a.setSelected(False)
    QCoreApplication.processEvents()
    assert a.control_pivot_ring.isVisible() is False
    assert a.control_pivot_label.isVisible() is False


def test_selection_indicator_shows_for_free_node():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    n = TwistNodeItem()
    win.scene.addItem(n)

    n.setSelected(True)
    QCoreApplication.processEvents()

    assert getattr(n, 'control_pivot_ring', None) is not None
    assert n.control_pivot_ring.isVisible() is True
    assert getattr(n, 'control_pivot_label', None) is not None
    assert n.control_pivot_label.isVisible() is True
    assert n.control_pivot.brush().color() == SELECTED_COLOR

    # Selection keeps pivot at fixed 10px device-space size
    assert n.control_pivot.rect().width() == CONTROL_PIVOT_DIAM
