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
    from unittest.mock import patch
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    canvas = window.canvas
    event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(10, 10), QPoint(10, 10), Qt.NoModifier)
    with patch.object(api, "open_context_menu", wraps=api.open_context_menu) as mock_open:
        try:
            canvas.contextMenuEvent(event)
        except RecursionError:
            pytest.fail("RecursionError: contextMenuEvent and open_context_menu are calling each other recursively.")
        mock_open.assert_called_once_with(event)
        assert event.isAccepted()
    window.close()
