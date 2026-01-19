import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF, QEvent
from PySide6.QtGui import QKeyEvent
from ui.main_window import MainWindow
from api.manager import APIManager
from unittest.mock import MagicMock

def test_all_ui_events_routed_to_input_system(qtbot):
    """
    Contract: All relevant UI events (mouse and key) must be routed to InputSystem.handle_canvas_event or eventFilter.
    """
    app = QApplication.instance() or QApplication([])
    # Patch InputSystem to monitor calls
    from ui.input_system import InputSystem
    input_system = InputSystem()
    input_system.handle_canvas_event = MagicMock(wraps=input_system.handle_canvas_event)
    input_system.eventFilter = MagicMock(wraps=input_system.eventFilter)
    # Inject patched InputSystem into APIManager
    APIManager._instance = None
    api = APIManager.get_instance()
    api.input_system = input_system
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    canvas = window.canvas
    # Mouse events
    center = canvas.viewport().rect().center()
    mouse_pos = center
    qtbot.mousePress(canvas.viewport(), Qt.LeftButton, pos=mouse_pos)
    move_pos = center + type(center)(10, 10)
    qtbot.mouseMove(canvas.viewport(), pos=move_pos)
    qtbot.mouseRelease(canvas.viewport(), Qt.LeftButton, pos=move_pos)
    qtbot.mouseDClick(canvas.viewport(), Qt.LeftButton, pos=mouse_pos)
    # Wheel event (simulate zoom)
    wheel_event = QEvent(QEvent.Wheel)
    QApplication.sendEvent(canvas.viewport(), wheel_event)
    # Key events
    key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier)
    QApplication.sendEvent(canvas.viewport(), key_event)
    key_event_release = QKeyEvent(QEvent.KeyRelease, Qt.Key_A, Qt.NoModifier)
    QApplication.sendEvent(canvas.viewport(), key_event_release)
    # Assert that mouse events were routed
    assert input_system.handle_canvas_event.call_count >= 3, "Not all mouse events routed to InputSystem.handle_canvas_event."
    # Assert that key events were routed
    assert input_system.eventFilter.call_count >= 2, "Not all key events routed to InputSystem.eventFilter."
    window.close()
