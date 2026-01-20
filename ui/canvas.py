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
        # Add button attribute if present in original_event
        if hasattr(original_event, 'button'):
            self.button = original_event.button()

class HarnessCanvas(QGraphicsView):
    def contextMenuEvent(self, event):
        print('[DEBUG] HarnessCanvas.contextMenuEvent called')
        api = APIManager.get_instance()
        if hasattr(api, 'open_context_menu'):
            print('[DEBUG] HarnessCanvas calling api.open_context_menu')
            api.open_context_menu(event)
        else:
            print('[DEBUG] HarnessCanvas: api has no open_context_menu')
        event.accept()
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._dispatch(event)
        super().mouseDoubleClickEvent(event)
    def dragEnterEvent(self, event):
        api = APIManager.get_instance()
        if hasattr(api, 'handle_drag_enter'):
            api.handle_drag_enter(event)
        event.accept()

    def dropEvent(self, event):
        api = APIManager.get_instance()
        if hasattr(api, 'handle_drop'):
            api.handle_drop(event)
        event.accept()
    def wheelEvent(self, event):
        # Zoom factor per wheel step
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        angle_delta = event.angleDelta().y()
        if angle_delta > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        elif angle_delta < 0:
            self.scale(zoom_out_factor, zoom_out_factor)
        else:
            super().wheelEvent(event)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Theme
        try:
            from ui.coordinates import THEME_FALLBACK
            self._theme = THEME_FALLBACK
        except Exception:
            self._theme = {"canvas_bg": "#2E2E2E", "grid_color": "#444444"}

        # Navigation
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Visuals
        from PySide6.QtGui import QColor
        self.setBackgroundBrush(QColor(self._theme.get("canvas_bg", "#2E2E2E")))

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        # Draw grid
        color = self._theme.get("grid_color", "#444444")
        from PySide6.QtGui import QColor
        grid_pen = QColor(color)
        painter.setPen(grid_pen)
        grid_size = 5.0
        left = int(rect.left()) - (int(rect.left()) % int(grid_size))
        top = int(rect.top()) - (int(rect.top()) % int(grid_size))
        right = int(rect.right())
        bottom = int(rect.bottom())
        x = left
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += grid_size
        y = top
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += grid_size

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
        """Forward event to InputSystem. Route right-clicks on device items to API for context menu."""
        api = APIManager.get_instance()
        if not api.input_system:
            return

        pos = qt_event.position()
        from PySide6.QtCore import QPointF, QPoint
        if isinstance(pos, QPointF):
            scene_pos = self.mapToScene(pos.toPoint())
        elif isinstance(pos, QPoint):
            scene_pos = self.mapToScene(pos)
        else:
            scene_pos = self.mapToScene(0, 0)

        item = self.scene.itemAt(scene_pos, self.transform())
        print(f'[HarnessCanvas._dispatch] scene_pos={scene_pos}, item={item}, type={type(item)}')
        evt = CanvasEvent(qt_event, scene_pos, scene_item=item, item_at=item)
        if hasattr(qt_event, 'button'):
            evt.button = qt_event.button()

        # Route all events, including right-clicks, through InputSystem
        api.input_system.handle_canvas_event(evt)