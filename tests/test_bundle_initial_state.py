from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow


def test_bundle_has_no_initial_elbow():
    # Ensure QApplication exists
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0)

    # Newly created bundle should have no explicit route points and thus no elbow handles
    assert b.route == []
    assert len(b.elbow_handles) == 0
    # The implicit handle was removed entirely; ensure no attribute exists
    assert getattr(b, 'handle', None) is None
