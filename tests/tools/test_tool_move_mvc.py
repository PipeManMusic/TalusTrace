import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QPointF, Qt
from tools.move_tool import MoveTool
 # CanvasEvent is no longer used; test only MoveTool and model/undo stack behavior
from core.device import Device
from api.manager import APIManager

@pytest.fixture
def api_and_tool(clean_api_singleton):
    api = clean_api_singleton
    tool = MoveTool()
    tool.api = api
    return api, tool

def test_move_tool_mvc_compliance(api_and_tool):
    api, tool = api_and_tool
    api.context.undo_stack.clear()
    import uuid
    device = Device(id=str(uuid.uuid4()), x=0.0, y=0.0)
    from core.harness import DeviceList
    with DeviceList.test_bypass():
        api.context.harness.devices.append(device)
    mock_item = MagicMock()
    mock_item.model = device
    mock_item.parentItem.return_value = None
    mock_item.setPos = MagicMock()
    # Subscribe to model_changed and call setPos when device moves
    def on_model_changed(data):
        item = data.get('item', None)
        if item and hasattr(item, 'id') and item.id == device.id:
            mock_item.setPos(QPointF(device.x, device.y))
    api.subscribe(on_model_changed)
    api.register_scene_item(device.id, mock_item)
    # Set initial drag position for mock item (test compatibility)
    mock_item._drag_initial_pos = (0.0, 0.0)
    input_system = api.input_system
    # Inject MoveTool for test compliance
    input_system._move_tool = tool
    # Pre-select the device so drag will be triggered
    api.select([device.id])
    # Patch setPos to ensure it's only called during model_changed
    with patch.object(mock_item, 'setPos', wraps=mock_item.setPos) as setpos_patch, \
         patch.object(api, 'move_device', wraps=api.move_device) as move_patch, \
         patch.object(api, 'dispatch', wraps=api.dispatch) as dispatch_patch:
        # Simulate drag via InputSystem
        evt_press = MagicMock()
        evt_press.type.return_value = 2  # QEvent.MouseButtonPress
        event_obj_press = MagicMock()
        event_obj_press.original_event = evt_press
        event_obj_press.scene_item = mock_item
        event_obj_press.scene_pos = QPointF(0, 0)
        input_system.handle_canvas_event(event_obj_press)

        evt_move = MagicMock()
        evt_move.type.return_value = 5  # QEvent.MouseMove
        event_obj_move = MagicMock()
        event_obj_move.original_event = evt_move
        event_obj_move.scene_item = mock_item
        event_obj_move.scene_pos = QPointF(10, 10)
        input_system.handle_canvas_event(event_obj_move)

        evt_release = MagicMock()
        evt_release.type.return_value = 3  # QEvent.MouseButtonRelease
        event_obj_release = MagicMock()
        event_obj_release.original_event = evt_release
        event_obj_release.scene_item = mock_item
        event_obj_release.scene_pos = QPointF(10, 10)
        input_system.handle_canvas_event(event_obj_release)

        # Assert APIManager.move_device was called with device.id
        move_patch.assert_called_with(device.id, 10.0, 10.0, commit=True)
        # Assert device position updated
        assert device.x == 10.0 and device.y == 10.0
        # Assert scene item position updated
        mock_item.setPos.assert_called_with(QPointF(10.0, 10.0))
        # Assert undo stack contains MoveCommand
        assert len(api.context.undo_stack) == 1
        cmd = api.context.undo_stack._undo_stack[0]
        from api.commands.move import MoveCommand
        assert isinstance(cmd, MoveCommand), f"Undo stack did not contain MoveCommand, got {type(cmd)}"
        assert cmd.new_pos == (10.0, 10.0)
        assert any('model_changed' in str(call) for call in dispatch_patch.call_args_list)
        # Undo/redo
        cmd = api.context.undo_stack._undo_stack[0]
        cmd.undo()
        assert device.x == 0.0 and device.y == 0.0
        mock_item.setPos.assert_any_call(QPointF(0.0, 0.0))
        cmd.redo()
        assert device.x == 10.0 and device.y == 10.0
        mock_item.setPos.assert_any_call(QPointF(10.0, 10.0))
