import math
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsLineItem
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtCore import Qt, QRectF, QLineF, Signal, QPointF
from talustrace.frontend.items import PinItem, DeviceItem

# CONSTANTS
GRID_SIZE = 20
GRID_COLOR = QColor(60, 60, 60)
BG_COLOR = QColor(30, 30, 30)

class HarnessScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-50000, -50000, 100000, 100000)

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, BG_COLOR)

        left = int(math.floor(rect.left() / GRID_SIZE) * GRID_SIZE)
        top = int(math.floor(rect.top() / GRID_SIZE) * GRID_SIZE)
        right = int(math.ceil(rect.right() / GRID_SIZE) * GRID_SIZE)
        bottom = int(math.ceil(rect.bottom() / GRID_SIZE) * GRID_SIZE)

        pen = QPen(GRID_COLOR, 1)
        painter.setPen(pen)
        for x in range(left, right + 1, GRID_SIZE):
            painter.drawLine(x, top, x, bottom)
        for y in range(top, bottom + 1, GRID_SIZE):
            painter.drawLine(left, y, right, y)

class HarnessView(QGraphicsView):
    
    canvas_clicked = Signal(float, float)
    wire_connected = Signal(object, object) # Signal (From_PinItem, To_PinItem)

    def __init__(self, scene=None):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        
        self.mode = "SELECT"
        
        # Tools
        self.ghost_item = None 
        self.temp_wire = None
        self.start_pin = None
        self.last_pan_pos = None

    # --- MODE: PLACE DEVICE ---
    def start_ghost(self, item, mode="PLACE_DEVICE"):
        self.stop_ghost()
        self.mode = mode
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.CrossCursor)
        self.ghost_item = item
        self.ghost_item.setOpacity(0.5)
        self.ghost_item.setZValue(100)
        self.ghost_item.setAcceptedMouseButtons(Qt.NoButton)
        self.scene().addItem(self.ghost_item)

    def stop_ghost(self):
        if self.ghost_item:
            self.scene().removeItem(self.ghost_item)
            self.ghost_item = None
        if self.temp_wire:
            self.scene().removeItem(self.temp_wire)
            self.temp_wire = None
            self.start_pin = None
            
        self.mode = "SELECT"
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCursor(Qt.ArrowCursor)

    # --- EVENTS ---
    def wheelEvent(self, event):
        zoom_in = 1.15
        zoom_out = 1 / zoom_in
        factor = zoom_in if event.angleDelta().y() > 0 else zoom_out
        self.scale(factor, factor)

    def mouseMoveEvent(self, event):
        if self.last_pan_pos:
            delta = event.position() - self.last_pan_pos
            self.last_pan_pos = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        pos = self.mapToScene(event.position().toPoint())

        # Logic 1: Moving a Ghost Device
        if self.mode == "PLACE_DEVICE" and self.ghost_item:
            snap_x = round(pos.x() / GRID_SIZE) * GRID_SIZE
            snap_y = round(pos.y() / GRID_SIZE) * GRID_SIZE
            self.ghost_item.setPos(snap_x, snap_y)
            
        # Logic 2: Dragging a Wire
        if self.mode == "WIRING" and self.temp_wire and self.start_pin:
            # Update end of line to follow mouse
            p1 = self.start_pin.get_scene_pos()
            self.temp_wire.setLine(QLineF(p1, pos))
            
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())

            # 1. Place Device
            if self.mode == "PLACE_DEVICE":
                snap_x = round(scene_pos.x() / GRID_SIZE) * GRID_SIZE
                snap_y = round(scene_pos.y() / GRID_SIZE) * GRID_SIZE
                self.canvas_clicked.emit(snap_x, snap_y)
                return 

            # 2. Wire Logic
            pin_clicked = None
            for item in self.scene().items(scene_pos):
                if isinstance(item, PinItem):
                    pin_clicked = item
                    break
                parent = item.parentItem()
                if isinstance(parent, PinItem):
                    pin_clicked = parent
                    break

            if pin_clicked:
                if self.mode != "WIRING":
                    self.start_wiring(pin_clicked)
                    return
                if pin_clicked != self.start_pin:
                    self.finish_wiring(pin_clicked)
                return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.last_pan_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def start_wiring(self, pin_item):
        self.mode = "WIRING"
        self.setDragMode(QGraphicsView.NoDrag)
        self.start_pin = pin_item
        
        # Create Ghost Wire
        self.temp_wire = QGraphicsLineItem()
        self.temp_wire.setPen(QPen(Qt.red, 2, Qt.DashLine))
        self.scene().addItem(self.temp_wire)

    def finish_wiring(self, end_pin):
        # Notify App to create real wire
        self.wire_connected.emit(self.start_pin, end_pin)
        
        # Cleanup
        self.stop_ghost()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.stop_ghost()
        super().keyPressEvent(event)