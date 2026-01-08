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
    assert tool.ghost_item is not None
    assert tool.ghost_item.x == 0
    
    # 2. Update Position (Ghost moves, Real object stays)
    tool.update(dx=10, dy=10)
    assert tool.ghost_item.x == 10
    assert dev.x == 0
    
    # 3. Commit (Real object moves via Command)
    cmd_mgr = CommandManager()
    cmd = tool.commit()
    cmd_mgr.execute(cmd, dev)
    
    assert dev.x == 10