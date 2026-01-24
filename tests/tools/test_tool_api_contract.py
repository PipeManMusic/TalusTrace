import pytest
from unittest.mock import MagicMock, patch
from tools.placement_tool import PlacementTool
from tools.move_tool import MoveTool
from tools.wire_tool import WireTool
from api.manager import APIManager

def test_tools_only_interact_with_api():
    """
    Contract: Tools must only interact with the API, not directly with undo stack, model, or UI.
    """
    api = APIManager.get_instance()
    api_mock = MagicMock(wraps=api)
    # Patch APIManager globally for all tools
    with patch('api.manager.APIManager.get_instance', return_value=api_mock):
        with patch.object(api_mock.context, 'undo_stack', wraps=api_mock.context.undo_stack) as undo_patch:
            # PlacementTool: simulate device placement via start_drag
            placement_tool = PlacementTool()
            placement_tool.api = api_mock
            placement_tool.active_type = 'device'
            scene_pos = MagicMock(x=lambda: 10.0, y=lambda: 20.0)
            placement_tool.start_drag(None, scene_pos)
            assert not undo_patch.push.called, "PlacementTool should not push directly to undo_stack"

            # MoveTool: simulate drag and drop
            move_tool = MoveTool()
            move_tool.api = api_mock
            device = MagicMock(id='D1', x=0.0, y=0.0)
            mock_item = MagicMock(model=device)
            move_tool.start_drag(mock_item, MagicMock(x=lambda: 0.0, y=lambda: 0.0))
            move_tool.update_drag(MagicMock(x=lambda: 50.0, y=lambda: 50.0))
            move_tool.finish_drag(MagicMock(x=lambda: 100.0, y=lambda: 100.0))
            assert not undo_patch.push.called, "MoveTool should not push directly to undo_stack"

            # WireTool: simulate wire creation
            with patch('api.manager.APIManager.get_instance', return_value=api_mock):
                wire_tool = WireTool()
                pin1 = MagicMock(id='P1', x=0.0, y=0.0)
                pin2 = MagicMock(id='P2', x=10.0, y=10.0)
                wire_tool.start_pin = pin1
                wire_tool.start_device = MagicMock(id='D1')
                wire_tool.state = "DRAGGING"
                wire_tool.current_mouse_pos = MagicMock(x=lambda: 10.0, y=lambda: 10.0)
                wire_tool.on_mouse_release(MagicMock())
                assert not undo_patch.push.called, "WireTool should not push directly to undo_stack"
