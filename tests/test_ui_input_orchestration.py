import pytest
from PySide6.QtCore import QPointF, Qt
from api.manager import APIManager


def test_default_tool_active_after_init(qtbot):
    """PH6-EVT.1: APIManager must have an active tool after initialization.

    If no tool is active, InputSystem silently drops all mouse events.
    This test would have caught the drag-to-move startup bug.
    """
    api = APIManager.get_instance()

    assert api.tool_manager is not None, "ToolManager not created"
    assert api.tool_manager.active_tool is not None, \
        "No active tool after APIManager init — all canvas interaction is dead"
    assert api.tool_manager.active_tool.__class__.__name__ == "SelectTool", \
        f"Default tool should be SelectTool, got {api.tool_manager.active_tool.__class__.__name__}"