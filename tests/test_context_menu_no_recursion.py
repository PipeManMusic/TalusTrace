import pytest
from unittest.mock import MagicMock
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtCore import QPoint, Qt

def test_context_menu_event_routed_to_api_no_recursion(qtbot, fresh_api, main_window):
    """
    Contract: Context menu event on canvas must be routed to APIManager.open_context_menu,
    and must not cause recursion or stack overflow. The API must handle the event, not call back into the UI event handler.
    """
    # Patch APIManager to track calls
    api = fresh_api
    api.open_context_menu = MagicMock(wraps=api.open_context_menu)
    
    # Simulate context menu event on the canvas
    canvas = main_window.canvas
    event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(10, 10), QPoint(10, 10), Qt.NoModifier)
    
    # Should not raise RecursionError
    try:
        canvas.contextMenuEvent(event)
    except RecursionError:
        pytest.fail("RecursionError: contextMenuEvent and open_context_menu are calling each other recursively.")
    
    # API should have handled the event exactly once
    api.open_context_menu.assert_called_once()
    # Check that it was called with event and item
    call_args = api.open_context_menu.call_args
    assert call_args[0][0] == event  # First positional arg is the event
    assert 'item' in call_args[1]  # Second arg is item as keyword
    # Event should be accepted
    assert event.isAccepted()
