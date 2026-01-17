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

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self):
        if not self.canvas:
            if hasattr(self.api, 'main_window'):
                self.canvas = self.api.main_window.canvas

        if not self.canvas: return

        self.canvas.setFocus()
        self.canvas.viewport().setMouseTracking(True)

        # Initialize Ghost at (0,0) - logic will update position on first move
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        ghost_model = Device(id="GHOST", x=0, y=0, meta=meta_defaults)

        self.ghost_item = DeviceItem(ghost_model, is_ghost=True)
        self.ghost_item.setZValue(2000)
        self.canvas.scene.addItem(self.ghost_item)

    def on_mouse_move(self, event):
        if not self.ghost_item: return
        try:
            # 1. Get Raw Position from Scene (already in MM)
            raw_x = event.scene_pos.x()
            raw_y = event.scene_pos.y()
            
            # 2. Ask API to apply Constraints (Snap to Grid)
            # This works regardless of what the grid size currently is
            x = self.api.settings.snap(raw_x)
            y = self.api.settings.snap(raw_y)
            
            self.ghost_item.setPos(x, y)
        except:
            self.ghost_item = None

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton: return

        # 1. Get Snap Coordinates
        raw_x = event.scene_pos.x()
        raw_y = event.scene_pos.y()
        
        x = self.api.settings.snap(raw_x)
        y = self.api.settings.snap(raw_y)
        
        from api.commands.device import AddDeviceCommand
        
        dev_id = f"DEV_{str(uuid.uuid4())[:8]}"
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        
        # Model stores MM directly
        new_device = Device(id=dev_id, x=x, y=y, meta=meta_defaults)
        
        cmd = AddDeviceCommand(new_device)
        self.api.context.undo_stack.push(cmd)

        # Select the new device in the core and update PropertyPanel
        from core.selection import SelectionManager
        SelectionManager().set_selection([new_device])
        self.api.dispatch("selection_changed", {"selection": [new_device], "tool": "PlacementTool"})

        # Also set Qt selection on the corresponding DeviceItem in the scene
        if self.canvas and self.canvas.scene:
            for item in self.canvas.scene.items():
                # DeviceItem has .model pointing to the device model
                if hasattr(item, 'model') and item.model is new_device:
                    if hasattr(item, 'setSelected'):
                        item.setSelected(True)
                        break

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