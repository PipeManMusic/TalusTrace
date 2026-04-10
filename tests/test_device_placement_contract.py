import pytest
from api.manager import APIManager
from tools.placement_tool import PlacementTool


def test_device_placement_activates_tool(qtbot):
    """Contract: Dispatching tool.add_generic_device activates PlacementTool
    through the real action registry and real ToolManager."""
    api = APIManager.get_instance()

    # Verify default tool is not PlacementTool
    assert not isinstance(api.tool_manager.active_tool, PlacementTool)

    # Dispatch through the real action system
    from api.actions import registry as action_registry
    action_registry.execute('tool.add_generic_device')

    # PlacementTool should now be active via real ToolManager
    assert isinstance(api.tool_manager.active_tool, PlacementTool), \
        f"Expected PlacementTool, got {type(api.tool_manager.active_tool).__name__}"
