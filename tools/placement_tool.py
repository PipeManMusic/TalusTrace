import uuid
from PySide6.QtCore import Qt
from ui.items import DeviceItem
from core.device import Device
from tools.base_tool import Tool
# REMOVE: from api.manager import APIManager (Causes Crash)

class PlacementTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.ghost_item = None

    def start(self):
        """Initializes the ghost visual."""
        # FIX: Import here
        from api.manager import APIManager
        
        if not self.canvas:
            api = APIManager.get_instance()
            if hasattr(api, 'main_window'):
                self.canvas = api.main_window.canvas

        if not self.canvas:
            return

        self.canvas.setFocus()
        self.canvas.viewport().setMouseTracking(True)
        
        # Determine starting position
        from PySide6.QtGui import QCursor
        view_pos = self.canvas.mapFromGlobal(QCursor.pos())
        scene_pos = self.canvas.mapToScene(view_pos)
        
        x = round(scene_pos.x() / 25.0) * 25.0
        y = round(scene_pos.y() / 25.0) * 25.0
        
        # Create Ghost
        ghost_model = Device(
            id="GHOST", 
            x=x, y=y, 
            meta={
                "width_mm": 40.0, 
                "height_mm": 30.0,
                "label": "Generic Device"
            }
        )
        # Assuming you have refactored ui/items, ensure DeviceItem is imported correctly above
        self.ghost_item = DeviceItem(ghost_model, is_ghost=True)
        self.ghost_item.setZValue(2000) 
        self.canvas.scene.addItem(self.ghost_item)

    def on_mouse_move(self, event):
        if not self.ghost_item:
            return
            
        try:
            pos = event.pos_mm
            x = round(pos.x() / 25.0) * 25.0
            y = round(pos.y() / 25.0) * 25.0
            self.ghost_item.setPos(x, y)
        except (RuntimeError, AttributeError):
            self.ghost_item = None

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton:
            return

        pos = event.pos_mm
        x = round(pos.x() / 25.0) * 25.0
        y = round(pos.y() / 25.0) * 25.0
        
        # FIX: Import here
        from api.manager import APIManager
        api = APIManager.get_instance()
        
        dev_id = f"DEV_{str(uuid.uuid4())[:8]}"
        
        new_device = Device(
            id=dev_id, 
            x=x, y=y,
            meta={
                "width_mm": 40.0, 
                "height_mm": 30.0,
                "label": "Generic Device",
                "manufacturer": "Generic"
            }
        )
        
        api.context.harness.devices.append(new_device)
        api.tool_manager.set_tool("select")
        
        # Refresh visuals
        self.canvas.load_harness(api.context.harness)

    def on_mouse_release(self, event):
        pass

    def deactivate(self):
        if self.ghost_item:
            try:
                if self.canvas and self.canvas.scene:
                    self.canvas.scene.removeItem(self.ghost_item)
            except RuntimeError:
                pass
            self.ghost_item = None
            
        if self.canvas:
            self.canvas.setMouseTracking(True)
            if self.canvas.scene:
                self.canvas.scene.update()

    def stop(self):
        self.deactivate()