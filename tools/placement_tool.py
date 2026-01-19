import uuid
from PySide6.QtCore import Qt, QPointF
from tools.base_tool import BaseTool
from core.device import Device
from core.metadata import MetadataManager

# Strict Headless Controller implementation ONLY
class PlacementTool(BaseTool):
    __guide__ = {
        "name": "Placement Tool",
        "description": "Place devices on the canvas.",
        "shortcuts": {}
    }

    def __init__(self):
        super().__init__()
        self.active_type = "generic"
        self.ghost_item = None
        self.current_pos = QPointF(0, 0)

    @property
    def scene(self):
        """Robust scene access for Headless/UI modes."""
        if hasattr(self.api, 'scene') and self.api.scene:
            return self.api.scene
        if hasattr(self.api, 'main_window') and self.api.main_window:
            return self.api.main_window.canvas.scene
        return None

    def start(self, *args, **kwargs):
        """Called when tool is activated."""
        if self.scene:
            # Create Ghost Item (View Logic)
            from ui.items.device import DeviceItem
            meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
            ghost_model = Device(id="GHOST", x=0, y=0, meta=meta_defaults)
            self.ghost_item = DeviceItem(ghost_model, is_ghost=True)
            self.ghost_item.setZValue(2000)
            self.scene.addItem(self.ghost_item)
            if hasattr(self.api, 'main_window') and self.api.main_window:
                self.api.main_window.canvas.setFocus()

    def on_mouse_move(self, event):
        # 1. Get Position
        pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
        # 2. Logic: Snap to Grid (Model Logic)
        if hasattr(self.api, 'settings'):
            x = self.api.settings.snap(pos.x())
            y = self.api.settings.snap(pos.y())
        else:
            x, y = pos.x(), pos.y()
        self.current_pos = QPointF(x, y)
        # 3. View Update: Move Ghost
        if self.ghost_item:
            try:
                self.ghost_item.setPos(x, y)
            except RuntimeError:
                self.ghost_item = None

    def on_mouse_press(self, event):
        # Button check (Headless safety)
        btn = getattr(event, 'button', None)
        if hasattr(event, 'original_event'):
            btn = event.original_event.button()
        if btn is not None and btn != Qt.LeftButton:
            return
        # Set current_pos from event if not already set
        pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else None)
        if pos is not None:
            if hasattr(self.api, 'settings'):
                x = self.api.settings.snap(pos.x())
                y = self.api.settings.snap(pos.y())
            else:
                x, y = pos.x(), pos.y()
            self.current_pos = QPointF(x, y)
        # 1. Commit to Model
        from api.commands.device import AddDeviceCommand
        dev_id = f"DEV_{str(uuid.uuid4())[:8]}"
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        new_device = Device(id=dev_id, x=self.current_pos.x(), y=self.current_pos.y(), meta=meta_defaults)
        cmd = AddDeviceCommand(new_device)
        if hasattr(self.api.context, 'undo_stack'):
            self.api.context.undo_stack.push(cmd)
        # 2. Reset / Switch Tool
        if hasattr(self.api.tool_manager, 'set_tool'):
            self.api.tool_manager.set_tool("select")

    def deactivate(self):
        # Cleanup View
        if self.ghost_item:
            try:
                if self.scene:
                    self.scene.removeItem(self.ghost_item)
            except RuntimeError:
                pass
            self.ghost_item = None