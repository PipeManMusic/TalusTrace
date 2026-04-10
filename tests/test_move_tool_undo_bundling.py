import pytest
from PySide6.QtCore import QPointF, Qt
from unittest.mock import MagicMock
from tools.move_tool import MoveTool
 # CanvasEvent is no longer used; test only MoveTool and model/undo stack behavior
from core.device import Device
from api.manager import APIManager

def test_move_tool_undo_bundling(qtbot, clean_api_singleton):
    """
    Unit test: MoveTool pushes exactly ONE MoveCommand to the undo stack
    on finish_drag, and real-time model updates happen during drag.
    """
    # 1. Setup
    api = clean_api_singleton
    
    # Create Device
    import uuid
    dev = Device(id=str(uuid.uuid4()), x=0, y=0)
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev)
    
    # Setup Tool
    tool = MoveTool()
    tool.api = api
    tool.start(dev)

    # Create and register a mock QGraphicsItem wrapper for the device
    mock_item = MagicMock()
    mock_item.model = dev
    mock_item.parentItem.return_value = None
    mock_item.setPos = MagicMock()
    mock_item.pos.return_value = QPointF(dev.x, dev.y)
    mock_item._drag_initial_pos = (dev.x, dev.y)
    # Subscribe to model_changed and call setPos when device moves
    def on_model_changed(data):
        item = data.get('item', None)
        if item and hasattr(item, 'id') and item.id == dev.id:
            mock_item.setPos(QPointF(dev.x, dev.y))
    api.subscribe(on_model_changed)
    api.register_scene_item(dev.id, mock_item)

    # Simulate Drag (0,0 -> 100,100)
    tool.start_drag(mock_item, QPointF(0, 0))
    tool.update_drag(QPointF(50, 50))
    assert dev.x == 50.0, "MoveTool failed real-time update requirement"
    tool.finish_drag(QPointF(100, 100))
    assert dev.x == 100.0
    # Assert scene item position updated
    mock_item.setPos.assert_called_with(QPointF(100.0, 100.0))
    # Undo stack should have exactly 1 command
    assert len(api.context.undo_stack) == 1, "VIOLATION: Undo Stack empty! MoveTool modified state but pushed no command."
    # Undo Integrity
    api.context.undo_stack.undo()
    assert dev.x == 0.0, "Undo failed to revert position to start."
    mock_item.setPos.assert_any_call(QPointF(0.0, 0.0))
