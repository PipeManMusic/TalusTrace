from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import PIVOT_HIT_RADIUS


def _close_enough(a, b, tol=0.5):
    return abs(a.x() - b.x()) < tol and abs(a.y() - b.y()) < tol


def test_ring_centers_on_source_and_target_nodes():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    src = b.source_node
    tgt = b.target_node

    # Select source, ensure ring centered on pivot
    src.setSelected(True)
    QCoreApplication.processEvents()
    src_ring_scene = src.mapToScene(src.control_pivot_ring.pos())
    src_pivot_scene = src.mapToScene(src.control_pivot.pos())
    assert _close_enough(src_ring_scene, src_pivot_scene)

    # Select target, ensure ring centered on pivot
    src.setSelected(False)
    tgt.setSelected(True)
    QCoreApplication.processEvents()
    tgt_ring_scene = tgt.mapToScene(tgt.control_pivot_ring.pos())
    tgt_pivot_scene = tgt.mapToScene(tgt.control_pivot.pos())
    assert _close_enough(tgt_ring_scene, tgt_pivot_scene)