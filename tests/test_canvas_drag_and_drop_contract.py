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

class DummyEvent:
    def __init__(self, mime_data=None, pos=None):
        self._pos = pos or MagicMock()
        self.mimeData = lambda: mime_data or MagicMock()
        self.pos = lambda: self._pos
        self.position = lambda: self._pos
        self.accept = MagicMock()
        self.ignore = MagicMock()
        self._type = 0
    def type(self):
        return self._type
    def acceptProposedAction(self):
        self.accept()
        def acceptProposedAction(self):
            self.accept()

def test_canvas_drag_and_drop_calls_api_manager(canvas, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    drag_event = DummyEvent()
    drop_event = DummyEvent()
    api_manager.handle_drag_enter = MagicMock()
    api_manager.handle_drop = MagicMock()
    canvas.dragEnterEvent(drag_event)
    api_manager.handle_drag_enter.assert_called_once_with(drag_event)
    canvas.dropEvent(drop_event)
    api_manager.handle_drop.assert_called_once_with(drop_event)
