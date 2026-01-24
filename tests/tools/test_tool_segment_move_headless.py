from tools.segment_move_tool import SegmentMoveTool
import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPointF

class MockEvent:
    def __init__(self, x, y):
        self.scene_pos = QPointF(x, y)

def test_segment_drag_realtime(fresh_api, create_test_wire):
    wire = create_test_wire([
        [0.0, 0.0],
        [0.0, 10.0],
        [10.0, 10.0],
        [10.0, 0.0]
    ])
    tool = SegmentMoveTool()
    tool.api = fresh_api
    fresh_api.tool_manager = MagicMock()
    # Start drag on segment 1-2, drag start at (0,10) using event
    tool.start(wire, 1, 2, event=MockEvent(0.0, 10.0))
    # Move mouse to (0, 15) (down by 5)
    event = MockEvent(0.0, 15.0)
    tool.on_mouse_move(event)
    assert wire.path_nodes[1] == [0.0, 15.0]
    assert wire.path_nodes[2] == [10.0, 15.0]
    assert wire.path_nodes[0] == [0.0, 0.0]
    assert wire.path_nodes[3] == [10.0, 0.0]

def test_segment_commit_undo(fresh_api, create_test_wire):
    wire = create_test_wire([
        [0.0, 0.0],
        [0.0, 10.0],
        [10.0, 10.0],
        [10.0, 0.0]
    ])
    tool = SegmentMoveTool()
    tool.api = fresh_api
    fresh_api.tool_manager = MagicMock()
    fresh_api.context.undo_stack = MagicMock()
    tool.start(wire, 1, 2, event=MockEvent(0.0, 10.0))
    event = MockEvent(0.0, 15.0)
    tool.on_mouse_move(event)
    tool.on_mouse_release(event)
    fresh_api.context.undo_stack.push.assert_called_once()
    assert fresh_api.tool_manager.set_tool.called
