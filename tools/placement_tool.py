import uuid
from PySide6.QtCore import Qt
from ui.items import DeviceItem
from core.device import Device
from tools.base_tool import Tool
from api.manager import APIManager

class PlacementTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.ghost_item = None

    def start(self):
        """Initializes the ghost visual."""
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
        
        ghost_model = Device(id="GHOST", x=x, y=y)
        self.ghost_item = DeviceItem(ghost_model, is_ghost=True)
        self.ghost_item.setZValue(2000) # Keep on top
        self.canvas.scene.addItem(self.ghost_item)

    def on_mouse_move(self, event):
        """Standard grid-snapping follower logic with C++ lifetime guard."""
        # PH7-FIX.1: Check if ghost exists before accessing
        if not self.ghost_item:
            return
            
        try:
            # PH7-FIX.2: Ensure logic is inside the method to avoid NameError
            pos = event.pos_mm
            x = round(pos.x() / 25.0) * 25.0
            y = round(pos.y() / 25.0) * 25.0
            
            # PH7-FIX.3: The try block catches race conditions during deletion
            self.ghost_item.setPos(x, y)
        except (RuntimeError, AttributeError):
            # If the C++ object was deleted while we were moving, clear reference
            self.ghost_item = None

    def on_mouse_press(self, event):
        """Commits the device and requests a tool switch via Manager."""
        if event.original_event.button() != Qt.LeftButton:
            return

        pos = event.pos_mm
        x = round(pos.x() / 25.0) * 25.0
        y = round(pos.y() / 25.0) * 25.0
        
        api = APIManager.get_instance()
        dev_id = f"DEV_{str(uuid.uuid4())[:8]}"
        new_device = Device(id=dev_id, x=x, y=y)
        
        api.context.harness.devices.append(new_device)
        
        # Request switch to selection mode; ToolManager will call deactivate()
        api.tool_manager.set_tool("select")
        
        # Trigger UI Refresh AFTER switching to ensure the ghost is gone
        self.canvas.load_harness(api.context.harness)

    def on_mouse_release(self, event):
        pass

    def deactivate(self):
        """Visual cleanup. The ToolManager handles the state transition."""
        if self.ghost_item:
            try:
                if self.canvas and self.canvas.scene:
                    self.canvas.scene.removeItem(self.ghost_item)
            except RuntimeError:
                pass
            self.ghost_item = None
            
        if self.canvas:
            self.canvas.setMouseTracking(True)

    def stop(self):
        self.deactivate()