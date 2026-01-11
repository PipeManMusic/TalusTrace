import uuid
from PySide6.QtCore import Qt
from ui.items import DeviceItem
from core.device import Device
from tools.base_tool import Tool
from core.metadata import MetadataManager
from api.commands.device import AddDeviceCommand

class PlacementTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.ghost_item = None
        self.active_type = "generic"

    def start(self):
        from api.manager import APIManager
        if not self.canvas:
            api = APIManager.get_instance()
            if hasattr(api, 'main_window'):
                self.canvas = api.main_window.canvas

        if not self.canvas: return

        self.canvas.setFocus()
        self.canvas.viewport().setMouseTracking(True)
        
        from PySide6.QtGui import QCursor
        view_pos = self.canvas.mapFromGlobal(QCursor.pos())
        scene_pos = self.canvas.mapToScene(view_pos)
        x = round(scene_pos.x() / 25.0) * 25.0
        y = round(scene_pos.y() / 25.0) * 25.0
        
        # Load Defaults from YAML
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        
        ghost_model = Device(id="GHOST", x=x, y=y, meta=meta_defaults)
        self.ghost_item = DeviceItem(ghost_model, is_ghost=True)
        self.ghost_item.setZValue(2000) 
        self.canvas.scene.addItem(self.ghost_item)

    def on_mouse_move(self, event):
        if not self.ghost_item: return
        try:
            pos = event.pos_mm
            x = round(pos.x() / 25.0) * 25.0
            y = round(pos.y() / 25.0) * 25.0
            self.ghost_item.setPos(x, y)
        except:
            self.ghost_item = None

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton: return

        pos = event.pos_mm
        x = round(pos.x() / 25.0) * 25.0
        y = round(pos.y() / 25.0) * 25.0
        
        from api.manager import APIManager
        api = APIManager.get_instance()
        
        dev_id = f"DEV_{str(uuid.uuid4())[:8]}"
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        
        new_device = Device(id=dev_id, x=x, y=y, meta=meta_defaults)
        
        # FIX: Use Command (Fixes Undo & Browser)
        cmd = AddDeviceCommand(new_device)
        api.context.undo_stack.push(cmd)
        
        api.tool_manager.set_tool("select")

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
