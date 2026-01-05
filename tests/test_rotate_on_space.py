from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QEvent, Qt
import pytest
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items import TwistNodeItem, TwistedBundleItem

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_space_rotates_selected_bundle_nodes(qapp):
    win = MainWindow(restore_policy="skip")
    bundle = win.add_twisted_bundle(10, 20, spacing=120)
    # select the bundle
    bundle.setSelected(True)
    s0 = bundle._start_point()
    # Send key press through view (use QApplication.sendEvent so eventFilter runs)
    evt = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.NoModifier)
    from PySide6.QtWidgets import QApplication as _QApp
    _QApp.sendEvent(win.view, evt)
    s1 = bundle._start_point()
    assert not (round(s0.x(), 6) == round(s1.x(), 6) and round(s0.y(), 6) == round(s1.y(), 6))


def test_space_rotates_selected_node(qapp):
    win = MainWindow(restore_policy="skip")
    node = TwistNodeItem(on_changed=None)
    win.scene.addItem(node)
    node.setSelected(True)
    h0 = node.get_pin_tip_scene_pos("H")
    evt = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.NoModifier)
    from PySide6.QtWidgets import QApplication as _QApp
    _QApp.sendEvent(win.view, evt)
    h1 = node.get_pin_tip_scene_pos("H")
    assert not (round(h0.x(), 6) == round(h1.x(), 6) and round(h0.y(), 6) == round(h1.y(), 6))
