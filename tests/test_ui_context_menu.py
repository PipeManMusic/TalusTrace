import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication
from ui.canvas import HarnessCanvas
from unittest.mock import MagicMock

def test_context_menu_request(qtbot):
    """PH5-INTER.2: Right-click should trigger context menu event."""
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    
    # Mock the method on this instance
    canvas.show_context_menu = MagicMock()
    
    # Simulate Right Click using specific Qt event to bypass viewport complexities in headless mode
    from PySide6.QtGui import QContextMenuEvent
    event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(100,100), QPoint(100,100))
    QApplication.sendEvent(canvas.viewport(), event)
    
    assert canvas.show_context_menu.called
