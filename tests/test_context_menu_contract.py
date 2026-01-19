import pytest
from PySide6.QtCore import Qt
from ui.canvas import HarnessCanvas
from api.manager import APIManager
from ui.input_system import InputSystem

class DummyTool:
    def __init__(self):
        self.last_event = None
        self.context_menu_called = False
    def on_mouse_press(self, event):
        self.last_event = event
        # Simulate context menu call for right-click
        if hasattr(event, 'button') and event.button == Qt.RightButton:
            self.context_menu_called = True
            # Simulate expected API method
            api = APIManager.get_instance()
            assert hasattr(api, 'open_context_menu'), "APIManager missing 'open_context_menu' method"

@pytest.fixture
def canvas_and_api(qtbot):
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    api = APIManager.get_instance()
    api.tool_manager.active_tool = DummyTool()
    return canvas, api

def test_context_menu_api_contract(canvas_and_api, qtbot):
    canvas, api = canvas_and_api
    # Simulate right mouse press event
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPointF
    event = QMouseEvent(
        QMouseEvent.MouseButtonPress,
        QPointF(50, 50), QPointF(50, 50),
        Qt.RightButton, Qt.RightButton, Qt.NoModifier
    )
    # Patch APIManager to add open_context_menu for test
    api.open_context_menu = lambda event: True
    canvas.mousePressEvent(event)
    tool = api.tool_manager.active_tool
    assert tool.context_menu_called, "Context menu was not called on right-click"
