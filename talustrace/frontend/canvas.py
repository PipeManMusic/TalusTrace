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
    def mousePressEvent(self, event):
        # Robust routing: if click lands on a pivot child (control_pivot/control_dot) or on
        # a TwistNodeItem, ensure the node receives the press so selection and pivot-anchored
        # dragging behavior is consistent from scene-level dispatch.
        try:
            from PySide6.QtCore import Qt
            pos = event.scenePos()
            # top-first list
            for it in self.items(pos):
                try:
                    data0 = it.data(0)
                except Exception:
                    data0 = None
                if data0 in ('control_pivot', 'control_dot'):
                    parent = it.parentItem()
                    if parent:
                        try:
                            # Mark which child was pressed so the parent can differentiate
                            parent._last_child_pressed = data0
                        except Exception:
                            pass
                        try:
                            # Deselect any bundles attached to this node so the node selection is visually primary
                            for b in list(parent.bundle_refs):
                                try:
                                    b.setSelected(False)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        try:
                            parent.setSelected(True)
                        except Exception:
                            pass
                        try:
                            parent.mousePressEvent(event)
                        except Exception:
                            pass
                        try:
                            event.accept()
                        except Exception:
                            pass
                        try:
                            # Clear auxiliary marker
                            del parent._last_child_pressed
                        except Exception:
                            pass
                        return
                # If the item itself is a TwistNodeItem, route to it
                try:
                    if it.__class__.__name__ == 'TwistNodeItem':
                        try:
                            for b in list(it.bundle_refs):
                                try:
                                    b.setSelected(False)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        try:
                            it.setSelected(True)
                        except Exception:
                            pass
                        try:
                            it.mousePressEvent(event)
                        except Exception:
                            pass
                        return
                except Exception:
                    pass
        except Exception:
            pass
        return super().mousePressEvent(event)
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
            try:
                self.scene().removeItem(self.temp_wire)
            except Exception:
                pass
            self.temp_wire = None
            self.start_pin = None

        # Also clean up any stray parentless temp wires that might have been orphaned
        try:
            self._cleanup_orphan_temp_wires()
        except Exception:
            pass
                
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
        try:
            if self.last_pan_pos:
                delta = event.position() - self.last_pan_pos
                self.last_pan_pos = event.position()
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
                return

            pos = self.mapToScene(event.position().toPoint())

            # Logic 1: Moving a ghost (device or bundle)
            if self.mode in ("PLACE_DEVICE", "PLACE_BUNDLE") and self.ghost_item:
                snap_x = round(pos.x() / GRID_SIZE) * GRID_SIZE
                snap_y = round(pos.y() / GRID_SIZE) * GRID_SIZE
                self.ghost_item.setPos(snap_x, snap_y)
                
            # Logic 2: Dragging a Wire
            if self.mode == "WIRING" and self.temp_wire and self.start_pin:
                # Update end of line to follow mouse
                p1 = self.start_pin.get_scene_pos()
                self.temp_wire.setLine(QLineF(p1, pos))

            # Logic 3: Proximity hover over node control pivot
            try:
                if self.mode == "SELECT" and self.scene():
                    self.update_pivot_hover_at_scene_pos(pos)
            except Exception:
                pass

        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            super().mouseMoveEvent(event)

    def update_pivot_hover_at_scene_pos(self, scene_pos):
        """Update proximity hover state for node pivots based on a scene coordinate."""
        from talustrace.frontend.items_baseline import PIVOT_HIT_RADIUS
        sr = PIVOT_HIT_RADIUS
        rect = QRectF(scene_pos.x() - sr, scene_pos.y() - sr, sr * 2, sr * 2)
        items = self.scene().items(rect)
        found_node = None
        for it in items:
            # Walk up to see if this item is a TwistNodeItem
            parent = it
            while parent and parent.__class__.__name__ != 'TwistNodeItem':
                parent = parent.parentItem()
            if parent:
                # Check distance to pivot
                try:
                    pivot_scene = parent.mapToScene(getattr(parent, '_pivot', parent._rect.center()))
                    dx = scene_pos.x() - pivot_scene.x()
                    dy = scene_pos.y() - pivot_scene.y()
                    if (dx*dx + dy*dy) <= (sr * sr):
                        found_node = parent
                        break
                except Exception:
                    pass
        # Clear previous hovered node(s)
        try:
            # Only one hover at a time; clear any nodes that are currently hovered but not the found one
            for item in list(self.scene().items()):
                try:
                    if item.__class__.__name__ == 'TwistNodeItem' and getattr(item, '_pivot_hover', False) and item is not found_node:
                        item.set_pivot_hover(False)
                except Exception:
                    pass
        except Exception:
            pass
        if found_node:
            try:
                found_node.set_pivot_hover(True)
            except Exception:
                pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())

            # 1. Place device/bundle
            if self.mode in ("PLACE_DEVICE", "PLACE_BUNDLE"):
                snap_x = round(scene_pos.x() / GRID_SIZE) * GRID_SIZE
                snap_y = round(scene_pos.y() / GRID_SIZE) * GRID_SIZE
                self.canvas_clicked.emit(snap_x, snap_y)
                return 

            # 2. Wire Logic
            pin_clicked = None
            for item in self.scene().items(scene_pos):
                if isinstance(item, PinItem):
                    # If parent is a TwistNode and the pin is on the reserved bundle side, ignore it
                    parent = item.parentItem()
                    if parent and parent.__class__.__name__ == 'TwistNodeItem':
                        # Avoid importing here to keep imports local to tests and runtime
                        if not parent.pin_connectable(item.model.id):
                            continue
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
        # Cleanup any prior orphaned temp wires before starting a new wiring operation
        try:
            self._cleanup_orphan_temp_wires()
        except Exception:
            pass

        self.mode = "WIRING"
        self.setDragMode(QGraphicsView.NoDrag)
        self.start_pin = pin_item
        
        # Create Ghost Wire
        self.temp_wire = QGraphicsLineItem()
        self.temp_wire.setPen(QPen(Qt.red, 2, Qt.DashLine))
        try:
            self.temp_wire.setData(0, 'temp_wire')
            self.temp_wire.setZValue(900)
        except Exception:
            pass
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

    def _cleanup_orphan_temp_wires(self):
        """Remove any parentless QGraphicsLineItem instances (likely orphaned temporary wires).
        This is a defensive cleanup to ensure ghost wires never persist in the scene accidentally."""
        try:
            items = list(self.scene().items()) if self.scene() else []
            for it in items:
                try:
                    if isinstance(it, QGraphicsLineItem) and it.parentItem() is None:
                        # Conservative removal: remove only dashed/red or data-tagged temp wires OR reasonably small lines
                        pen = it.pen() if hasattr(it, 'pen') else None
                        is_temp_tagged = False
                        try:
                            is_temp_tagged = it.data(0) == 'temp_wire'
                        except Exception:
                            is_temp_tagged = False
                        try:
                            is_dash_and_red = pen is not None and (pen.style() == Qt.DashLine) and (pen.color() == Qt.red)
                        except Exception:
                            is_dash_and_red = False
                        try:
                            bbox = it.sceneBoundingRect()
                        except Exception:
                            bbox = QRectF()

                        # Remove if tagged or dash+red or if bounding box is reasonably small
                        if is_temp_tagged or is_dash_and_red or (bbox.width() < 500 and bbox.height() < 500 and it.parentItem() is None):
                            try:
                                if it.scene():
                                    it.scene().removeItem(it)
                                    print(f"Cleanup: removed orphan line item: bbox={bbox}")
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass
