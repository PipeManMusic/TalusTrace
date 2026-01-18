import pytest
from core.device import Device
from infra.commands import CommandManager
# Target Implementation: tools/move_tool.py
from tools.move_tool import MoveTool

def test_move_tool_ghosting():
    dev = Device(id="D1", x=0, y=0)
    tool = MoveTool()

    # 1. Start Move
    tool.start(target=dev)
    # Ghost item is just an alias to the target in the new architecture
    assert tool.ghost_item is not None
    assert tool.ghost_item.x == 0

    # 2. Update Position
    # In the new Realtime architecture, the model updates immediately.
    tool.update(dx=10, dy=10)
    assert tool.ghost_item.x == 10
    assert dev.x == 10  # UPDATED: Expect realtime sync