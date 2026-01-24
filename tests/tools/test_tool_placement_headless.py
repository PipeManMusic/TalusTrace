import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF, Qt

class MockEvent:
    def __init__(self, x, y):
        self.scene_pos = QPointF(x, y)
        self.pos = lambda: QPointF(x, y)
        self.buttons = lambda: Qt.LeftButton
        self.button = Qt.LeftButton
        self.original_event = MagicMock()
        self.original_event.button.return_value = Qt.LeftButton

def test_placement_snapping_logic(fresh_api):
    from tools.placement_tool import PlacementTool
    
    tool = PlacementTool()
    tool.api = fresh_api # Inject API
    
    # Mock Settings for Snapping
    fresh_api.settings = MagicMock()
    fresh_api.settings.snap.side_effect = lambda x: round(x / 5.0) * 5.0 # Simple 5mm snap
    
    tool.start()
    
    # Act: Move mouse to (12, 12) -> Should snap to (10, 10)
    event = MockEvent(12.0, 12.0)
    tool.on_mouse_move(event)
    
    # Assert coordinates specifically (Fixes QPointF vs Tuple mismatch)
    assert tool.current_pos.x() == 10.0
    assert tool.current_pos.y() == 10.0

def test_placement_commit(fresh_api):
    from tools.placement_tool import PlacementTool
    
    tool = PlacementTool()
    tool.api = fresh_api
    fresh_api.context.undo_stack = MagicMock()
    fresh_api.tool_manager = MagicMock() # Prevent actual switching
    fresh_api.settings = MagicMock()
    fresh_api.settings.snap.side_effect = lambda x: x # No snap for this test
    
    # Ensure tool has a current position (needed by on_mouse_press)
    tool.current_pos = QPointF(50.0, 50.0)
    
    event = MockEvent(50.0, 50.0)
    tool.on_mouse_press(event)
    
    # Assert Command Pushed
    assert fresh_api.context.undo_stack.push.called
    cmd = fresh_api.context.undo_stack.push.call_args[0][0]
    # Accept either AddDeviceCommand or MockCommand for test
    assert cmd.__class__.__name__ in ("AddDeviceCommand", "MockCommand")
    
    # Verify the device in the command has correct coords
    assert cmd.device.x == 50.0
    assert cmd.device.y == 50.0
    
    # Verify tool switch to 'select'
    assert fresh_api.tool_manager.set_tool.called