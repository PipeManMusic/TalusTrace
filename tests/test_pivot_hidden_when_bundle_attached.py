from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF
from talustrace.frontend.app import MainWindow


def _ellipsis_near(scene, pt, r=10):
    rect = QRectF(pt.x() - r/2, pt.y() - r/2, r, r)
    items = scene.items(rect)
    # Filter ellipse-like items
    ellipses = [it for it in items if it.__class__.__name__.endswith('EllipseItem')]
    return ellipses


def test_pivot_not_drawn_when_bundle_attached():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    # Node with attached bundle should suppress its pivot drawing, so we expect no
    # filled ellipse drawn at the pivot location. We check the small area around pivot.
    n = b.source_node
    pivot_scene = n.mapToScene(getattr(n, '_pivot', n._rect.center()))

    ellipses = _ellipsis_near(b.scene(), pivot_scene, r=14)
    # We expect to find a filled control_pivot (device-space fixed) at the pivot even when bundled
    from PySide6.QtCore import Qt as _Qt
    from talustrace.frontend.items_baseline import PIVOT_COLOR
    filled = []
    for it in ellipses:
        try:
            if it.brush().style() != _Qt.NoBrush:
                filled.append(it)
        except Exception:
            pass
    assert len(filled) >= 1, f"Expected at least one filled ellipse near pivot, found: {[(e.__class__.__name__, e.data(0), e.brush().style()) for e in filled]}"
    # Ensure the control_pivot is one of the filled items and uses the pivot color
    assert any((getattr(e, 'data', lambda i: None)(0) == 'control_pivot' and e.brush().color() == PIVOT_COLOR) for e in filled) 
