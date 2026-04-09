"""
Wire tool and state classes for wire creation and manipulation in Talus Trace.
Implements wire drawing, pin hit testing, and event handling.
"""
import uuid
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtGui import QPen, QColor
from tools.base_tool import Tool
from ui.items.pin import PinItem 
from core.wire import Wire

class WireToolState:
    """
    State constants for WireTool.
    """
    IDLE = "IDLE"
    DRAGGING = "DRAGGING"

class WireTool(Tool):
    """
    Tool for wire creation and manipulation.
    """
    def __init__(self, harness=None):
        """
        Initialize the WireTool.
        Args:
            harness: Optional harness model.
        """
        super().__init__()
        self.harness = harness
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        self.ghost_line = None
        self.current_mouse_pos = QPointF(0, 0)

    @property
    def api(self):
        """
        Get the APIManager instance for the tool.
        """
        from api.manager import APIManager
        return APIManager.get_instance()

    @property
    def scene(self):
        """
        Robust scene access for Headless/UI modes.
        """
        if hasattr(self.api, 'scene') and self.api.scene:
            return self.api.scene
        if hasattr(self.api, 'main_window') and self.api.main_window:
            return self.api.main_window.canvas.scene
        return None

    def start(self):
        """
        Start the wire tool and set cursor.
        """
        if hasattr(self.api, 'main_window') and self.api.main_window:
            self.api.main_window.canvas.setCursor(Qt.CrossCursor)

    def begin_wire_from_pin(self, pin_model, device_model, scene_pos):
        """
        Begin wire drawing from a specific pin (e.g. on double-click).
        Sets up the same state as clicking a pin in IDLE mode.
        Args:
            pin_model: The pin to start from.
            device_model: The device owning the pin.
            scene_pos: Current scene position for the ghost line endpoint.
        """
        self.start_pin = pin_model
        self.start_device = device_model
        self.state = "DRAGGING"
        if self.scene:
            self.ghost_line = QGraphicsLineItem()
            pen = QPen(QColor(0, 255, 0), 0, Qt.DashLine)
            pen.setCosmetic(True)
            self.ghost_line.setPen(pen)
            start_pos = self._get_pin_scene_pos(pin_model, device_model)
            self.ghost_line.setLine(start_pos.x(), start_pos.y(), scene_pos.x(), scene_pos.y())
            self.scene.addItem(self.ghost_line)

    def _get_pin_at_pos(self, scene_pos):
        """
        Hit test for PinItem under cursor in World Space (MM).
        Args:
            scene_pos: Position in scene coordinates.
        Returns:
            Tuple of (pin, device_model) or (None, None).
        """
        scene = self.scene
        if not scene: return None, None
        
        # Handle MagicMock vs Real Scene
        items = scene.items(scene_pos)
        
        for item in items:
            if isinstance(item, PinItem):
                device_item = item.parentItem()
                if device_item and hasattr(device_item, 'model'):
                    return item.pin, device_item.model
        return None, None

    def on_mouse_press(self, event):
        """
        Handle mouse press event for wire creation.
        Args:
            event: Mouse event.
        """
        # Determine button safely (Headless vs UI)
        if hasattr(event, 'original_event') and event.original_event:
            if event.original_event.button() != Qt.LeftButton:
                return
        
        pin, device = self._get_pin_at_pos(event.scene_pos)

        if self.state == "IDLE":
            if pin and device:
                self.start_pin = pin
                self.start_device = device
                self.state = "DRAGGING"
                
                # Visual Feedback (Only if UI is present)
                if self.scene:
                    self.ghost_line = QGraphicsLineItem()
                    pen = QPen(QColor(0, 255, 0), 0, Qt.DashLine)
                    pen.setCosmetic(True)
                    self.ghost_line.setPen(pen)
                    start_pos = self._get_pin_scene_pos(pin, device)
                    self.ghost_line.setLine(start_pos.x(), start_pos.y(), event.scene_pos.x(), event.scene_pos.y())
                    self.scene.addItem(self.ghost_line)
            else:
                pass

        elif self.state == "DRAGGING":
            if pin and device:
                if device == self.start_device and pin == self.start_pin:
                    return
                self._create_wire(self.start_device, self.start_pin, device, pin)
                self._reset()
            else:
                self._reset()

    def on_mouse_move(self, event):
        """
        Handle mouse move event for wire creation and update ghost line.
        Args:
            event: Mouse event.
        """
        self.current_mouse_pos = event.scene_pos
        
        if self.state == "DRAGGING" and self.ghost_line:
            try:
                if not self.ghost_line.scene(): 
                    self.ghost_line = None
                    return
                
                start_pos = self.ghost_line.line().p1()
                
                # Snap to target pin if hovering
                target_pin, target_device = self._get_pin_at_pos(event.scene_pos)
                if target_pin and target_device:
                    end_pos = self._get_pin_scene_pos(target_pin, target_device)
                else:
                    end_pos = event.scene_pos
                
                self.ghost_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            except RuntimeError:
                self.ghost_line = None

    def _create_wire(self, dev1, pin1, dev2, pin2):
        """
        Create a new wire between two devices and pins, and push AddWireCommand.
        Args:
            dev1: First device.
            pin1: First pin.
            dev2: Second device.
            pin2: Second pin.
        """
        p1 = self._get_pin_scene_pos(pin1, dev1)
        p2 = self._get_pin_scene_pos(pin2, dev2)
        path_nodes = [[p1.x(), p1.y()], [p2.x(), p2.y()]]
        wire_id = str(uuid.uuid4())
        new_wire = Wire(
            id=wire_id,
            from_conn=dev1.id,
            from_pin=pin1.id,
            to_conn=dev2.id,
            to_pin=pin2.id,
            type="STANDARD",
            path_nodes=path_nodes
        )
        # Add wire via API contract (undoable AddWireCommand)
        self.api.add_wire(new_wire)
        
        # Reset tool
        if hasattr(self.api.tool_manager, 'set_tool'):
            self.api.tool_manager.set_tool('select')

    def _get_pin_scene_pos(self, pin_model, device_model):
        """
        Get the scene position of a pin on a device.
        Args:
            pin_model: Pin model object.
            device_model: Device model object.
        Returns:
            QPointF position in scene coordinates.
        """
        scene = self.scene
        if not scene: return QPointF(0,0)
        
        # Logic for Headless Mocking support
        if hasattr(scene, 'items'):
            for item in scene.items():
                if isinstance(item, PinItem) and hasattr(item, 'pin') and item.pin.id == pin_model.id:
                    # In headless, mapToScene might be mocked or we accept item pos
                    if hasattr(item, 'mapToScene'):
                        return item.mapToScene(0.0, 0.0)
                    return item.pos()
        return QPointF(0,0)

    def _reset(self):
        """
        Reset the wire tool state and remove ghost line.
        """
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        
        if self.ghost_line:
            try:
                if self.scene and self.ghost_line.scene() == self.scene:
                    self.scene.removeItem(self.ghost_line)
            except RuntimeError:
                pass
            self.ghost_line = None

    def deactivate(self):
        """
        Deactivate the wire tool and reset its state.
        """
        self._reset()
        if hasattr(self.api, 'main_window') and self.api.main_window:
            from PySide6.QtCore import Qt
            self.api.main_window.canvas.setCursor(Qt.ArrowCursor)