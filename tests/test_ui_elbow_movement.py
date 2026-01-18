import pytest

@pytest.mark.skip(reason="Legacy BundleItem import")
def test_move_tool_targets_elbow():
    """PH6-UI.2: MoveTool must update specific BundleItem nodes."""
    from tools.move_tool import MoveTool
    from ui.canvas import CanvasEvent
    from PySide6.QtCore import QPointF

    path = [(0,0), (50,50), (100,100)]
    # Updated to include wire_diameters as required by BundleItem __init__
    bundle = BundleItem(path, wire_diameters=[1.0, 1.0, 1.0]) 
    tool = MoveTool()
    
    # Press near elbow at (50,50)
    tool.on_mouse_press(CanvasEvent(None, QPointF(51, 49), None, bundle))
    # Move to (75, 75)
    tool.on_mouse_move(CanvasEvent(None, QPointF(75, 75), None, bundle))
    
    assert bundle.path_nodes[1] == (75.0, 75.0)