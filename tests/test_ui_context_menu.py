import pytest
from PySide6.QtCore import Qt, QPoint
from ui.canvas import HarnessCanvas
from core.device import Device
from core.models import Harness

from unittest.mock import MagicMock

def test_context_menu_request(qtbot):
    """PH5-INTER.2: Right-click should trigger context menu event."""
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    
    # Mock the menu builder
    canvas.show_context_menu = MagicMock()
    
    # Simulate Right Click
    qtbot.mouseClick(canvas.viewport(), Qt.RightButton, pos=QPoint(100,100))
    
    assert canvas.show_context_menu.called