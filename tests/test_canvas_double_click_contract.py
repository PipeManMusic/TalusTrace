import pytest
from unittest.mock import MagicMock
from ui.canvas import HarnessCanvas
from api.manager import APIManager

@pytest.fixture
def canvas(qtbot):
    c = HarnessCanvas()
    qtbot.addWidget(c)
    return c

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()


from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QPointF, Qt

# Contract: Canvas must dispatch mouseDoubleClickEvent to APIManager or InputSystem
# and enforce event contract (button, position, accept/ignore)
def test_canvas_double_click_contract(canvas, api_manager, monkeypatch):
    # Patch APIManager.get_instance to return our test instance
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    # Patch input_system to track calls
    api_manager.input_system = MagicMock()
    api_manager.input_system.handle_canvas_event = MagicMock()

    # Create a real QMouseEvent for double-click
    event = QMouseEvent(
        QMouseEvent.MouseButtonDblClick,
        QPointF(10, 10),
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier
    )
    canvas.mouseDoubleClickEvent(event)
    api_manager.input_system.handle_canvas_event.assert_called_once()
    evt = api_manager.input_system.handle_canvas_event.call_args[0][0]
    assert hasattr(evt, 'button')
    assert hasattr(evt, 'scene_pos')
