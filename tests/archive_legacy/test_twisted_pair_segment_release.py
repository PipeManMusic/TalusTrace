import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_segment_release_no_crash(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=200)

    # There is a single segment handle even without elbows
    sh = bundle.segment_handles[0]

    # Map to view coords
    sh_scene = sh.mapToScene(sh.boundingRect().center())
    view_pos = win.view.mapFromScene(sh_scene)

    # Do a press/move/release — there should be no exception (i.e., no crash)
    QTest.mousePress(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y())))
    QTest.qWait(10)
    QTest.mouseMove(win.view.viewport(), QPoint(int(view_pos.x()), int(view_pos.y() + 5)))
    QTest.qWait(10)
    QTest.mouseRelease(win.view.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(int(view_pos.x()), int(view_pos.y() + 5)))

    # If we reach here, the release handler executed successfully
    assert True
