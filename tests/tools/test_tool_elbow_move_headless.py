import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF, Qt

class MockEvent:
    def __init__(self, x, y):
        self.scene_pos = QPointF(x, y)
        self.buttons = lambda: Qt.LeftButton

def test_elbow_drag_realtime(fresh_api, create_test_wire):
    """PH6-EVT.3: Elbow drag must update model coordinates in realtime."""
    # 1. Setup Data
    wire = create_test_wire(nodes=[[0, 0], [50, 0], [100, 0]])
    
    # 2. Setup Tool
    from tools.elbow_move_tool import ElbowMoveTool
    tool = ElbowMoveTool()
    tool._api_instance = fresh_api
    
    # 3. Start Drag on Elbow 1 (at 50,0)
    # The tool is started programmatically by the SelectTool (simulated here)
    tool.start(wire, 1)
    
    # 4. Act: Move Mouse to (50, 50)
    event = MockEvent(50, 50)
    tool.on_mouse_move(event)
    
    # 5. Assert: Model Updated Immediately
    assert wire.path_nodes[1] == [50.0, 50.0]
    # Endpoints should remain unchanged
    assert wire.path_nodes[0] == [0.0, 0.0]
    assert wire.path_nodes[2] == [100.0, 0.0]

def test_elbow_commit_undo(fresh_api, create_test_wire):
    """PH5-CMD.2: Releasing mouse must push a command to undo stack."""
    wire = create_test_wire(nodes=[[0, 0], [50, 0], [100, 0]])
    
    from tools.elbow_move_tool import ElbowMoveTool
    tool = ElbowMoveTool()
    tool._api_instance = fresh_api
    
    # Mock Undo Stack
    fresh_api.context.undo_stack = MagicMock()
    
    # Perform Drag Operation
    tool.start(wire, 1)
    tool.on_mouse_move(MockEvent(50, 50))
    tool.on_mouse_release(MockEvent(50, 50))
    
    # Assert Command Pushed
    assert fresh_api.context.undo_stack.push.called
    cmd = fresh_api.context.undo_stack.push.call_args[0][0]
    assert cmd.__class__.__name__ == "MoveElbowCommand"