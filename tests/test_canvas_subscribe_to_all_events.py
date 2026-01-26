import pytest
from unittest.mock import MagicMock
from ui.canvas import HarnessCanvas
from api.manager import APIManager
from infra.context import Context
from core.harness import Harness

def test_canvas_subscribe_to_all_events(qtbot):
    """
    Ensure the canvas stays in sync with the model by subscribing to all API events.
    This test simulates a model mutation event and an undo/redo event,
    and asserts that the canvas refresh logic is triggered.
    """
    # Setup API and context
    api = APIManager.get_instance()
    api.context = Context()
    harness = Harness()
    api.context.harness = harness
    # Patch load_harness to track calls
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    canvas.load_harness = MagicMock()
    # Simulate model_changed event
    api.context.observer.dispatch('model_changed', {'action': 'add', 'item': object()})
    # Should call on_model_changed, but not load_harness for model_changed
    assert not canvas.load_harness.called, "Canvas should not reload harness on model_changed, only on undo/redo."
    # Simulate undo event
    api.context.observer.dispatch('undo', {})
    assert canvas.load_harness.called, "Canvas did not reload harness on undo event."
    canvas.load_harness.reset_mock()
    # Simulate redo event
    api.context.observer.dispatch('redo', {})
    assert canvas.load_harness.called, "Canvas did not reload harness on redo event."
