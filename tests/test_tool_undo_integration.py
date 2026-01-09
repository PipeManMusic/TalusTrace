import pytest
from unittest.mock import patch, MagicMock
from tools.move_tool import MoveTool
from api.manager import APIManager

def test_move_tool_pushes_command():
    """PH5-CMD.2: Move Tool should push MoveCommand on mouse release."""
    api = APIManager.get_instance()
    # Mock the Undo Stack via Context
    api.context.undo_stack = MagicMock()
    
    tool = MoveTool()

    # Create a dummy Device with x, y attributes and model_dump method
    class DummyDevice:
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y
        def model_dump(self):
            return {'x': self.x, 'y': self.y}

    device = DummyDevice(0, 0)
    tool.start(device)
    # Optionally simulate a move
    tool.ghost_item.x = 10
    tool.ghost_item.y = 10

    # On release, it should NOT modify model directly, but push command
    tool.on_mouse_release(None)

    # Verify push was called
    assert api.context.undo_stack.push.called

    # Inspect the command args (optional, depends on MoveCommand impl)
    args = api.context.undo_stack.push.call_args[0][0]
    assert args.__class__.__name__ == "MoveCommand"