from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsItem
from ui.items import DeviceItem
from api.actions import registry
from core.device import Device
from tools.base_tool import Tool

class PlacementTool(Tool):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.ghost_item = None
        self.device = None

    def start(self):
        # Ensure canvas grabs focus and enable mouse tracking for ghost placement
        self.canvas.setFocus()
        self.canvas.viewport().setMouseTracking(True)
        self.canvas.setMouseTracking(True)
        scene = self.canvas.scene
        from PySide6.QtGui import QCursor
        view_pos = self.canvas.mapFromGlobal(QCursor.pos())
        scene_rect = self.canvas.viewport().rect()
        if not scene_rect.contains(view_pos):
            center_view = self.canvas.viewport().rect().center()
            scene_pos = self.canvas.mapToScene(center_view)
        else:
            scene_pos = self.canvas.mapToScene(view_pos)
        x = round(scene_pos.x() / 25.0) * 25.0
        y = round(scene_pos.y() / 25.0) * 25.0
        self.device = Device(id="GHOST", x=x, y=y, pins=[], meta={"width_mm": 40.0, "height_mm": 30.0})
        self.ghost_item = DeviceItem(self.device, is_ghost=True)
        self.ghost_item.setOpacity(0.5)
        self.ghost_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.ghost_item.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.ghost_item.setAcceptedMouseButtons(Qt.NoButton)
        self.ghost_item.setZValue(1000)
        self.ghost_item.setPos(x, y)
        scene.addItem(self.ghost_item)

    def on_mouse_move(self, event):
        # event: CanvasEvent
        pos = getattr(event, 'pos_mm', None)
        if pos is not None:
            x = round(pos.x() / 25.0) * 25.0
            y = round(pos.y() / 25.0) * 25.0
            self.ghost_item.setPos(x, y)

    def on_mouse_press(self, event):
        # event: CanvasEvent
        pos = getattr(event, 'pos_mm', None)
        if pos is None:
            return
        x = round(pos.x() / 25.0) * 25.0
        y = round(pos.y() / 25.0) * 25.0
        from api.manager import APIManager
        api = APIManager.get_instance()
        harness = api.context.harness
        import uuid
        dev_id = f"DEV_{str(uuid.uuid4())[:8]}"
        from core.device import Device
        device = Device(id=dev_id, x=x, y=y, pins=[], meta={"width_mm": 40.0, "height_mm": 30.0})
        harness.devices.append(device)
        # Remove ghost
        if self.ghost_item:
            self.canvas.scene.removeItem(self.ghost_item)
            self.ghost_item = None
        # Sync UI
        window = None
        try:
            from PySide6.QtWidgets import QApplication
            window = QApplication.activeWindow()
        except Exception:
            pass
        if window and hasattr(window, 'canvas'):
            window.canvas.load_harness(harness)
            # Auto-zoom to new device
            for item in window.canvas.scene.items():
                if hasattr(item, 'device') and getattr(item.device, 'id', None) == dev_id:
                    window.canvas.fitInView(item.sceneBoundingRect(), Qt.KeepAspectRatio)
                    item.setSelected(True)
                    break
        self.deactivate()
        if window and hasattr(window, 'canvas'):
            window.canvas.load_harness(harness)
            # Auto-zoom to new device
            for item in window.canvas.scene.items():
                if hasattr(item, 'device') and getattr(item.device, 'id', None) == dev_id:
                    window.canvas.fitInView(item.sceneBoundingRect(), Qt.KeepAspectRatio)
                    item.setSelected(True)
                    break
        self.deactivate()
    def deactivate(self):
        # Use APIManager to set tool back to select for global sync
        from api.manager import APIManager
        api = APIManager.get_instance()
        api.tool_manager.set_tool("select")
        self.canvas.setMouseTracking(True)

    def stop(self):
        # Return to selection tool
        from tools.select_tool import SelectTool
        self.canvas.set_active_tool(SelectTool(self.canvas))
