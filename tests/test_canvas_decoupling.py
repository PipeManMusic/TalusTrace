import pytest
from unittest.mock import MagicMock, patch
from ui.main_window import MainWindow
from api.manager import APIManager
from PySide6.QtCore import Qt

def test_canvas_handoff_to_input_system(qtbot):
    """PH6-EVT.2: HarnessCanvas must hand off events to InputSystem."""
    window = MainWindow()
    qtbot.add_widget(window)
    canvas = window.canvas
    
    # 1. Mock the InputSystem
    mock_input_sys = MagicMock()
    APIManager.get_instance().input_system = mock_input_sys
    
    # 2. Trigger a mouse press on the canvas
    qtbot.mousePress(canvas.viewport(), Qt.LeftButton)
    
    # 3. Verify handoff occurred
    # handle_canvas_event should be called by mousePressEvent
    assert mock_input_sys.handle_canvas_event.called, \
        "Canvas did not hand off event to InputSystem"
    
    # Verify the object passed is a CanvasEvent
    args, _ = mock_input_sys.handle_canvas_event.call_args
    assert args[0].__class__.__name__ == "CanvasEvent"