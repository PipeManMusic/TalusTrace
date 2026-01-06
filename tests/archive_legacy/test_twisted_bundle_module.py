from PySide6.QtWidgets import QApplication
from talustrace.frontend.twisted_bundle import TwistedBundleItem
from talustrace.frontend.app import MainWindow


def test_twisted_bundle_facade_and_endpoints():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=120)

    # Ensure the returned bundle is an instance of the public facade class
    assert isinstance(b, TwistedBundleItem)

    # Start/end markers are optional; ensure endpoints are available via API
    # (visual markers were removed to avoid stray ellipses in renders)
    # If present, they should be valid; otherwise, ensure _start_point/_end_point work
    if getattr(b, 'start_marker', None) is not None:
        assert getattr(b, 'end_marker', None) is not None

    # Confirm finalize_attachment left nodes with a bundle side reserved
    a = b.source_node
    c = b.target_node
    assert getattr(a, '_bundle_side', None) is not None
    assert getattr(c, '_bundle_side', None) is not None

    # Start and end points should be valid scene points
    start = b._start_point()
    end = b._end_point()
    assert start is not None
    assert end is not None
