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
        self.position = lambda: self._pos  # For compatibility with HarnessCanvas._dispatch
        self.accept = MagicMock()
        self.ignore = MagicMock()
        self._type = 0  # Default event type

    def type(self):
        return self._type

# Contract: Canvas must dispatch dragEnterEvent and dropEvent to APIManager
# and enforce event contract (mimeData, pos, accept/ignore)
def test_canvas_drag_and_drop_contract(canvas, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    drag_event = DummyEvent()
    drop_event = DummyEvent()

    # Patch APIManager to track calls
    api_manager.handle_drag_enter = MagicMock()
    api_manager.handle_drop = MagicMock()

    # Simulate dragEnterEvent
    canvas.dragEnterEvent(drag_event)
    api_manager.handle_drag_enter.assert_called_once_with(drag_event)
    assert hasattr(drag_event, 'mimeData')
    assert hasattr(drag_event, 'pos')
    assert callable(drag_event.accept)
    assert callable(drag_event.ignore)

    # Simulate dropEvent
    canvas.dropEvent(drop_event)
    api_manager.handle_drop.assert_called_once_with(drop_event)
    assert hasattr(drop_event, 'mimeData')
    assert hasattr(drop_event, 'pos')
    assert callable(drop_event.accept)
    assert callable(drop_event.ignore)
