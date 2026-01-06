from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from PySide6.QtCore import QCoreApplication


def test_control_pivot_visible_at_multiple_zooms():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(60,60,spacing=160)
    QCoreApplication.processEvents()

    pivots = [b.source_node.control_pivot, b.target_node.control_pivot]

    found_any = False
    for s in [1.0, 2.0, 4.0, 8.0]:
        win.view.resetTransform()
        win.view.scale(s, s)
        QCoreApplication.processEvents()
        for i, cp in enumerate(pivots, 1):
            # Map pivot center to view coords and center the view on it to isolate visibility
            br = cp.mapToScene(cp.boundingRect()).boundingRect()
            center_scene = br.center()
            win.view.centerOn(center_scene)
            QCoreApplication.processEvents()
            img = win.view.grab().toImage()
            center_view = win.view.mapFromScene(center_scene)
            x = int(center_view.x())
            y = int(center_view.y())
            w = img.width(); h = img.height()
            # examine an 11x11 pixel window around pivot center for non-background color
            count = 0
            for yy in range(max(0, y-5), min(h, y+6)):
                for xx in range(max(0, x-5), min(w, x+6)):
                    c = img.pixelColor(xx, yy)
                    if not ((c.red()==255 and c.green()==255 and c.blue()==255) or (c.red()==48 and c.green()==48 and c.blue()==48)):
                        count += 1
            assert count > 0, f'Pivot {i} not visible at scale {s} (pixel window count={count})'
            found_any = True
    assert found_any
