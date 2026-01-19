from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QMouseEvent
from api.manager import APIManager

class CanvasEvent:
    def __init__(self, original_event, scene_pos, scene_item=None, item_at=None):
        self.original_event = original_event
        self.scene_pos = scene_pos
        self.scene_item = scene_item 
        self.item_at = item_at 

class HarnessCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Navigation
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Visuals
        self.setBackgroundBrush(Qt.darkGray)

    def load_harness(self, harness):
        """Populate scene with items from model."""
        self.scene.clear()
        api = APIManager.get_instance()
        
        # Devices
        from ui.items.device import DeviceItem
        for dev in getattr(harness, 'devices', []):
            item = DeviceItem(dev)
            self.scene.addItem(item)
            api.register_scene_item(dev.id, item)

        # Wires
        from ui.items.wire import WireItem
        for wire in getattr(harness, 'wires', []):
            item = WireItem(wire)
            self.scene.addItem(item)
            api.register_scene_item(wire.id, item)

    def zoom_extents(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isNull(): return
        pad = max(rect.width(), rect.height()) * 0.1
        rect.adjust(-pad, -pad, pad, pad)
        self.fitInView(rect, Qt.KeepAspectRatio)

    # --- Tool Event Dispatching ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            super().mousePressEvent(event)
            return
        self._dispatch(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self._dispatch(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            super().mouseReleaseEvent(event)
            return
        self._dispatch(event)
        super().mouseReleaseEvent(event)

    def _dispatch(self, qt_event):
        """Forward event to InputSystem."""
        api = APIManager.get_instance()
        if not api.input_system:
            return

        # Convert to Screen/Scene Coordinates
        scene_pos = self.mapToScene(qt_event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        
        # Wrap in CanvasEvent
        evt = CanvasEvent(qt_event, scene_pos, scene_item=item, item_at=item)
        
        # Handoff to InputSystem (The Fix)
        api.input_system.handle_canvas_event(evt)