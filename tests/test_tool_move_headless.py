import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF, Qt

class MockEvent:
    """Simulates a QGraphicsSceneMouseEvent for headless testing."""
    def __init__(self, pos_x, pos_y, button=Qt.LeftButton):
        self.scene_pos = QPointF(pos_x, pos_y)
        self.button = button

def test_move_tool_calculates_delta_and_calls_api(fresh_api, create_test_wire):
    """
    Verifies that the MoveTool calculates the drag distance (delta)
    and sends a move command to the API.
    """
    # 1. Setup: Create a wire and select it
    wire = create_test_wire()
    fresh_api.select([wire.id])
    
    # 2. Setup Tool
    from tools.move_tool import MoveTool
    tool = MoveTool()
    tool._api_instance = fresh_api  # Inject headless API
    
    # Mock the API move method to verify it gets called
    fresh_api.move_selection = MagicMock()
    
    # 3. Act: Start Drag at (0,0)
    start_evt = MockEvent(0, 0)
    # Mock scene.itemAt to return a mock with .model for hit test
    mock_item = MagicMock()
    mock_item.model = wire
    fresh_api.scene.itemAt.return_value = mock_item
    
    tool.on_mouse_press(start_evt)
    
    # 4. Act: Move to (10, 5)
    move_evt = MockEvent(10, 5)
    tool.on_mouse_move(move_evt)
    
    # 5. Assert: API was called with the correct delta
    # Delta = Current(10, 5) - Start(0, 0) = (10, 5)
    fresh_api.move_selection.assert_called_with(delta=(10.0, 5.0))
    
    # Verify internal state updated for continuous dragging
    assert tool.last_pos.x() == 10
    assert tool.last_pos.y() == 5