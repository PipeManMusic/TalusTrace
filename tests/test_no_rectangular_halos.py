from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow


def test_no_rectangular_halos_present():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)

    # Walk the scene items and ensure no rectangular halo siblings exist on devices/nodes
    for it in win.scene.items():
        cls = it.__class__.__name__
        if cls in ('DeviceItem', 'TwistNodeItem'):
            assert getattr(it, 'halo', None) is None
        if cls == 'TwistedBundleItem':
            # Bundle-level halo path should not exist
            assert getattr(it, 'halo_path', None) is None
