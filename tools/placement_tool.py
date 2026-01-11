import uuid
from PySide6.QtCore import Qt
from ui.items import DeviceItem
from core.device import Device
from tools.base_tool import Tool
from core.metadata import MetadataManager

class PlacementTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.ghost_item = None
        self.active_type = "generic"

    def start(self):
        from api.manager import APIManager
        self.api = APIManager.get_instance()
        
        # Ensure we have a valid canvas reference
        if not self.canvas:
            if hasattr(self.api, 'main_window'):
                self.canvas = self.api.main_window.canvas

        if not self.canvas: return

        self.canvas.setFocus()
        self.canvas.viewport().setMouseTracking(True)
        
        # 1. Get accurate initial position from the Mouse Event if possible,
        # otherwise rely on current cursor position mapped to scene.
        from PySide6.QtGui import QCursor
        view_pos = self.canvas.mapFromGlobal(QCursor.pos())
        scene_pos = self.canvas.mapToScene(view_pos)
        
        # 2. Snap immediately
        x = self.api.transformer.snap_to_grid(scene_pos.x())
        y = self.api.transformer.snap_to_grid(scene_pos.y())
        
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        ghost_model = Device(id="GHOST", x=x, y=y, meta=meta_defaults)
        
        self.ghost_item = DeviceItem(ghost_model, is_ghost=True)
        self.ghost_item.setZValue(2000) 
        self.canvas.scene.addItem(self.ghost_item)

    def on_mouse_move(self, event):
        if not self.ghost_item: return
        try:
            # event.pos_mm is the SCENE position (in pixels)
            raw_x = event.pos_mm.x()
            raw_y = event.pos_mm.y()
            
            # Snap to the calculated grid
            x = self.api.transformer.snap_to_grid(raw_x)
            y = self.api.transformer.snap_to_grid(raw_y)
            
            self.ghost_item.setPos(x, y)
        except:
            self.ghost_item = None

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton: return

        # Snap the final click location
        x = self.api.transformer.snap_to_grid(event.pos_mm.x())
        y = self.api.transformer.snap_to_grid(event.pos_mm.y())
        
        from api.commands.device import AddDeviceCommand
        
        dev_id = f"DEV_{str(uuid.uuid4())[:8]}"
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        
        new_device = Device(id=dev_id, x=x, y=y, meta=meta_defaults)
        
        cmd = AddDeviceCommand(new_device)
        self.api.context.undo_stack.push(cmd)
        
        # Switch back to Select Tool after placement
        self.api.tool_manager.set_tool("select")

    def on_mouse_release(self, event): pass

    def deactivate(self):
        if self.ghost_item:
            try:
                if self.canvas and self.canvas.scene:
                    self.canvas.scene.removeItem(self.ghost_item)
            except: pass
            self.ghost_item = None
        if self.canvas:
            self.canvas.setMouseTracking(True)
            self.canvas.scene.update()