def test_interaction_snaps_to_grid():
    """PH6-UI.1: MoveTool must snap coordinates to 25mm increments."""
    from tools.move_tool import MoveTool
    from core.device import Device
    from ui.items import DeviceItem
    from ui.canvas import CanvasEvent
    from PySide6.QtCore import QPointF

    dev = Device(id="SNAP_DEV", x=0, y=0)
    item = DeviceItem(dev)
    tool = MoveTool()
    
    # Drag to 38.5, 12.0 -> Should snap to 25.0, 0.0
    event = CanvasEvent(None, QPointF(38.5, 12.0), None, item)
    tool.on_mouse_move(event)
    
    assert dev.x == 25.0
    assert dev.y == 0.0