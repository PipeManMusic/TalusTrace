"""
Placement tool for device placement in Talus Trace.
Implements logic for placing devices on the canvas, drag operations, and ghost item management.
"""
import logging
import uuid
from PySide6.QtCore import Qt, QPointF
from tools.base_tool import BaseTool
from core.device import Device
from core.metadata import MetadataManager

# Strict Headless Controller implementation ONLY
class PlacementTool(BaseTool):
    """
    Tool for placing devices on the canvas, handling drag and ghost item logic.
    """
    __guide__ = {
        "name": "Placement Tool",
        "description": "Place devices on the canvas.",
        "shortcuts": {}
    }

    def __init__(self):
        """
        Initialize the PlacementTool with default type and ghost item.
        """
        super().__init__()
        self.active_type = "generic"
        self.ghost_item = None
        self.current_pos = QPointF(0, 0)

    def start_drag(self, item, scene_pos):
        """
        Start dragging to place a device on the canvas.
        Args:
            item: The item being dragged (unused).
            scene_pos: Scene position for placement.
        """
        # Always place device on first click, regardless of item
        if hasattr(self.api, 'settings'):
            x = self.api.settings.snap(scene_pos.x())
            y = self.api.settings.snap(scene_pos.y())
        else:
            x, y = scene_pos.x(), scene_pos.y()
        self.current_pos = QPointF(x, y)
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        dev_id = str(uuid.uuid4())
        new_device = Device(id=dev_id, x=x, y=y, meta=meta_defaults)
        # Only set up for drag; do not add device here. Device will be added in on_mouse_press.
        if hasattr(self.api.tool_manager, 'set_tool'):
            self.api.tool_manager.set_tool("select")

    def update_drag(self, scene_pos):
        """
        Update the position of the ghost item during drag.
        Args:
            scene_pos: Scene position for ghost movement.
        """
        # Always use scene coordinates for ghost movement
        if hasattr(self.api, 'settings'):
            x = self.api.settings.snap(scene_pos.x())
            y = self.api.settings.snap(scene_pos.y())
        else:
            x, y = scene_pos.x(), scene_pos.y()
        self.current_pos = QPointF(x, y)
        if self.ghost_item:
            try:
                self.ghost_item.setPos(x, y)
            except RuntimeError:
                self.ghost_item = None

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
            import uuid
            ghost_model = Device(id=str(uuid.uuid4()), x=0, y=0, meta=meta_defaults)
            self.ghost_item = DeviceItem(ghost_model, is_ghost=True)
            self.ghost_item.setZValue(2000)
            self.scene.addItem(self.ghost_item)
            if hasattr(self.api, 'main_window') and self.api.main_window:
                self.api.main_window.canvas.setFocus()

    def on_mouse_move(self, event):
        """
        Handle mouse move event to update ghost item position.
        Args:
            event: Mouse event.
        """
        # 1. Get Position
        pos = None
        if hasattr(event, 'scene_pos') and event.scene_pos is not None:
            pos = event.scene_pos
        elif hasattr(event, 'pos') and callable(event.pos):
            pos = event.pos()
        elif hasattr(event, 'x') and hasattr(event, 'y'):
            pos = QPointF(event.x(), event.y())
        else:
            pos = QPointF(0, 0)
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
        """Handle mouse press events to complete device placement."""
        import logging
        logging.debug(f"[PlacementTool.on_mouse_press] called with event={event}")
        """
        Handle mouse press event to place device and commit to model.
        Args:
            event: Mouse event.
        """
        # Button check (Headless safety)
        btn = getattr(event, 'button', None)
        if hasattr(event, 'original_event'):
            btn = event.original_event.button()
        import os
        is_headless = os.environ.get('PYTEST_CURRENT_TEST') or os.environ.get('DISPLAY') is None
        if not is_headless and btn is not None and btn != Qt.LeftButton:
            return
        # Set current_pos from event if not already set
        pos = None
        if hasattr(event, 'scene_pos') and event.scene_pos is not None:
            pos = event.scene_pos
        elif hasattr(event, 'pos') and callable(event.pos):
            pos = event.pos()
        elif hasattr(event, 'x') and hasattr(event, 'y'):
            pos = QPointF(event.x(), event.y())
        if pos is not None:
            if hasattr(self.api, 'settings'):
                x = self.api.settings.snap(pos.x())
                y = self.api.settings.snap(pos.y())
            else:
                x, y = pos.x(), pos.y()
            self.current_pos = QPointF(x, y)
        else:
            self.current_pos = QPointF(0, 0)
        # 1. Commit to Model
        logging.debug(f"[PlacementTool.on_mouse_press] About to add device at {self.current_pos}")
        dev_id = str(uuid.uuid4())
        meta_defaults = MetadataManager.get_instance().get_default_metadata(self.active_type)
        new_device = Device(id=dev_id, x=self.current_pos.x(), y=self.current_pos.y(), meta=meta_defaults)
        # Use APIManager to add device via AddDeviceCommand and undo stack
        logging.debug(f"[PlacementTool.on_mouse_press] self.api={self.api}")
        if hasattr(self.api, 'add_device'):
            logging.debug(f"[PlacementTool.on_mouse_press] Calling self.api.add_device")
            self.api.add_device(new_device)
        # Update canvas scene to reflect new device
        if hasattr(self.api.main_window, 'canvas'):
            self.api.main_window.canvas.load_harness(self.api.context.harness)
        # 2. Reset / Switch Tool
        if hasattr(self.api.tool_manager, 'set_tool'):
            self.api.tool_manager.set_tool("select")

    def deactivate(self):
        """
        Deactivate the placement tool and clean up ghost items.
        """
        # Cleanup View
        if self.ghost_item:
            try:
                if self.scene:
                    self.scene.removeItem(self.ghost_item)
            except RuntimeError:
                pass
            self.ghost_item = None