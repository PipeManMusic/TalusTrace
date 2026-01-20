import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtCore import QPoint, Qt
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import MagicMock

def test_canvas_context_menu_no_recursion(qtbot):
    """
    Contract: Context menu event on canvas must be routed to APIManager.open_context_menu,
    must not cause recursion, and must be accepted. The API must handle the event, not call back into the UI event handler.
    """
    app = QApplication.instance() or QApplication([])
    api = APIManager.get_instance()
    # Patch APIManager.open_context_menu to monitor calls and prevent recursion
    orig_open_context_menu = api.open_context_menu
    api.open_context_menu = MagicMock(wraps=orig_open_context_menu)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    canvas = window.canvas
    # Simulate context menu event on the canvas
    event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(10, 10), QPoint(10, 10), Qt.NoModifier)
    try:
        canvas.contextMenuEvent(event)
    except RecursionError:
        pytest.fail("RecursionError: contextMenuEvent and open_context_menu are calling each other recursively.")
    # API should have handled the event exactly once
    api.open_context_menu.assert_called_once_with(event)
    # Event should be accepted
    assert event.isAccepted()
    window.close()
