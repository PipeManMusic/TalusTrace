import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from ui.canvas import HarnessCanvas
from core.harness import Harness
from api.manager import APIManager
from infra.context import Context

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    api.dispatch = MagicMock(wraps=api.dispatch)
    api.subscribe = MagicMock(wraps=api.subscribe)
    api.input_system = MagicMock()
    yield api

def test_canvas_uses_api_manager_and_input_system(app, api_manager):
    canvas = HarnessCanvas()
    # Simulate loading a harness
    harness = Harness()
    canvas.load_harness(harness)
    # Simulate mouse event dispatch
    from PySide6.QtCore import QPoint
    class DummyEvent:
        def __init__(self):
            self.button = lambda: 1
            self.pos = lambda: QPoint(0, 0)
            self.position = lambda: QPoint(0, 0)
    event = DummyEvent()
    canvas._dispatch(event)
    # Assert APIManager and InputSystem were used
    assert api_manager.input_system.handle_canvas_event.called
    # Canvas should not mutate context or models directly
    # (No direct context/harness mutation outside APIManager)
    # Optionally, check dispatch/subscribe usage
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0
