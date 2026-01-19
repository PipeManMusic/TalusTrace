import pytest
from PySide6.QtCore import Qt
from ui.canvas import HarnessCanvas
from api.manager import APIManager
from ui.input_system import InputSystem

class DummyTool:
    def __init__(self):
        self.last_event = None
    def on_mouse_press(self, event):
        self.last_event = event
        # Check for button attribute
        assert hasattr(event, 'button'), "CanvasEvent missing 'button' attribute"
        # Check for scene_pos attribute
        assert hasattr(event, 'scene_pos'), "CanvasEvent missing 'scene_pos' attribute"

@pytest.fixture
def canvas_and_api(qtbot):
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    api = APIManager.get_instance()
    api.input_system = InputSystem()
    # Set DummyTool as active_tool in ToolManager
    api.tool_manager.active_tool = DummyTool()
    return canvas, api

def test_canvas_event_has_button_and_scene_pos(canvas_and_api, qtbot):
    canvas, api = canvas_and_api
    # Simulate mouse press event
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPointF, Qt, QPoint
    # Use Qt 6 constructor signature
    event = QMouseEvent(
        QMouseEvent.MouseButtonPress,
        QPointF(50, 50), QPointF(50, 50),
        Qt.LeftButton, Qt.LeftButton, Qt.NoModifier
    )
    canvas.mousePressEvent(event)
    # Check that DummyTool received a CanvasEvent with required attributes
    tool = api.tool_manager.active_tool
    assert tool.last_event is not None, "Tool did not receive event"
    assert hasattr(tool.last_event, 'button'), "CanvasEvent missing 'button' attribute"
    assert hasattr(tool.last_event, 'scene_pos'), "CanvasEvent missing 'scene_pos' attribute"
