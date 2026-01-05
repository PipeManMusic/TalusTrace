from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow


def _items_near(scene, pt, r=6):
    rect = QRectF(pt.x() - r/2, pt.y() - r/2, r, r)
    return scene.items(rect)


def test_no_extra_ellipse_near_bundle_elbow():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0)

    # At creation there should be no explicit route points and no stray ellipse items
    assert b.route == []
    items = _items_near(b.scene(), b.elbow_pos, r=12)

    # Filter for ellipse-like items: QGraphicsEllipseItem or subclasses
    ellipse_items = [it for it in items if it.__class__.__name__.endswith('EllipseItem')]

    # If the implicit handle is hidden there should be no ellipse items at the elbow
    assert len(ellipse_items) == 0, f"Found unexpected ellipse items near elbow: {[ (i.__class__.__name__, i.data(0)) for i in ellipse_items ]}"
