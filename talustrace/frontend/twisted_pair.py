from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsRectItem, QGraphicsPathItem, QGraphicsSceneMouseEvent, QGraphicsEllipseItem, QStyle
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

class TwistAnchorItem(QGraphicsItem):
    def mousePressEvent(self, event):
        """
        On right-click, rotate the anchor by 90 degrees. Otherwise, allow normal drag/move behavior.
        """
        if event.button() == Qt.RightButton:
            self.rotate_90()
            event.accept()
        else:
            super().mousePressEvent(event)
    def __init__(self, pos, parent=None, side=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.radius = 5  # 10px diameter matches theme
        self.setPos(*pos)
        self.side = side  # 'a' or 'b'
        self.setAcceptHoverEvents(True)
        self.setZValue(10)
        # Create two pins and two leaders as children of the anchor
        self.pins = []
        self.leaders = []
        for i in range(2):
            pin = QGraphicsEllipseItem(-3, -3, 6, 6, self)  # 6px diameter circle
            pin.setBrush(QBrush(Qt.gray))
            self.pins.append(pin)
            leader = QGraphicsLineItem(self)
            leader.setPen(QPen(Qt.black, 3, Qt.SolidLine))
            self.leaders.append(leader)

    def hoverEnterEvent(self, event):
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.update()
        super().hoverLeaveEvent(event)

    def rotate_90(self):
        """
        Increment this anchor's rotation by 90 degrees (modulo 360),
        update the corresponding model field (rotation_a or rotation_b),
        and trigger a layout refresh on the parent TwistedPairItem.
        """
        parent = self.parentItem()
        if not parent or not hasattr(parent, "model"):
            return
        model = parent.model
        if self.side == 'a':
            model.rotation_a = (getattr(model, 'rotation_a', 0) + 90) % 360
        elif self.side == 'b':
            model.rotation_b = (getattr(model, 'rotation_b', 0) + 90) % 360
        if hasattr(parent, "update_layout"):
            parent.update_layout()

    def boundingRect(self):
        r = self.radius
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def paint(self, painter, option, widget=None):
        brush = QBrush(Qt.orange)
        try:
            from talustrace.frontend.theme_tokens import theme_tokens
            brush = QBrush(QColor(theme_tokens.get("anchor_fill", "orange")))
        except Exception:
            pass
        if option.state & QStyle.State_MouseOver:
            brush = QBrush(brush.color().lighter(150))
        if option.state & QStyle.State_Selected:
            brush = QBrush(Qt.white)
        painter.setBrush(brush)
        painter.setPen(QPen(QColor("black")))
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        # Only trigger layout update after the position has actually changed
        if change == QGraphicsItem.ItemPositionHasChanged:
            parent = self.parentItem()
            if parent and hasattr(parent, "update_layout"):
                parent.update_layout()
        return super().itemChange(change, value)

class DoubleHelixPathItem(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path1 = QPainterPath()
        self.path2 = QPainterPath()
        self.color1 = QColor(Qt.red)
        self.color2 = QColor(Qt.blue)
        self._rect = QRectF(0, 0, 1, 1)

    def set_strand_colors(self, color1: QColor, color2: QColor):
        self.color1 = color1
        self.color2 = color2
        self.update()

    def update_geometry(self, start: QPointF, end: QPointF):
        from PySide6.QtCore import QPointF
        self.prepareGeometryChange()
        amp = 5.0
        wavelength = 20.0
        s = (start.x(), start.y())
        e = (end.x(), end.y())
        strand1, strand2 = calculate_double_helix(s, e, amp, wavelength)
        self.path1 = QPainterPath()
        self.path2 = QPainterPath()
        if strand1:
            self.path1.moveTo(QPointF(*strand1[0]))
            for pt in strand1[1:]:
                self.path1.lineTo(QPointF(*pt))
        if strand2:
            self.path2.moveTo(QPointF(*strand2[0]))
            for pt in strand2[1:]:
                self.path2.lineTo(QPointF(*pt))
        self._rect = self.path1.boundingRect().united(self.path2.boundingRect())

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.color1, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(self.path1)
        painter.setPen(QPen(self.color2, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(self.path2)

    def path(self):
        # For testing: return the union of both paths
        combined = QPainterPath(self.path1)
        combined.addPath(self.path2)
        return combined

class TwistedPairItem(QGraphicsObject):
    def __init__(self, model: TwistedPair, parent=None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.anchor_a = TwistAnchorItem(model.node_a, self, side='a')
        self.anchor_b = TwistAnchorItem(model.node_b, self, side='b')
        self.helix = DoubleHelixPathItem(self)
        # Ensure initial layout reflects model state (e.g., rotation_b)
        self.update_layout()



    def update_layout(self):
        """
        Snap anchor to grid. Pins use (-20,20) and (-20,-20) offsets, rotated by anchor rotation. Pin positions are local to anchor.
        Centralize color logic: both anchors' pins/leaders and helix strands are colored according to model wire_id_1/2.
        """
        from PySide6.QtGui import QTransform, QPen, QBrush, QColor
        if not hasattr(self, "anchor_a") or not hasattr(self, "anchor_b"):
            return

        def snap_point(pt):
            return QPointF(round(pt.x() / 20) * 20, round(pt.y() / 20) * 20)

        def rotated_offsets(rotation):
            base = [QPointF(-20, 20), QPointF(-20, -20)]
            t = QTransform()
            t.rotate(rotation)
            return [t.map(offset) for offset in base]

        def points_close(p1, p2, eps=0.01):
            return (abs(p1.x() - p2.x()) < eps) and (abs(p1.y() - p2.y()) < eps)

        # --- Color logic ---
        def color_for_wire(wire_id, default):
            if wire_id is None:
                return QColor(default)
            # Example: use blue for 1, red for 2, else fallback
            if wire_id == 1:
                return QColor("blue")
            if wire_id == 2:
                return QColor("red")
            return QColor(default)

        color1 = color_for_wire(getattr(self.model, 'wire_id_1', None), 'gray')
        color2 = color_for_wire(getattr(self.model, 'wire_id_2', None), 'gray')

        # Layout for anchor_a
        pos_a_scene = self.anchor_a.scenePos()
        snap_a_scene = snap_point(pos_a_scene)
        if not points_close(pos_a_scene, snap_a_scene):
            snap_a_local = self.mapFromScene(snap_a_scene)
            self.anchor_a.setPos(snap_a_local)
        rot_a = getattr(self.model, 'rotation_a', 0) % 360
        offsets_a = rotated_offsets(rot_a)
        for i, (pin, leader) in enumerate(zip(self.anchor_a.pins, self.anchor_a.leaders)):
            color = color1 if i == 0 else color2
            pin.setBrush(QBrush(color))
            leader.setPen(QPen(color, 3, Qt.SolidLine))
            pin.setPos(offsets_a[i])
            leader.setLine(0, 0, offsets_a[i].x(), offsets_a[i].y())

        # Layout for anchor_b
        pos_b_scene = self.anchor_b.scenePos()
        snap_b_scene = snap_point(pos_b_scene)
        if not points_close(pos_b_scene, snap_b_scene):
            snap_b_local = self.mapFromScene(snap_b_scene)
            self.anchor_b.setPos(snap_b_local)
        rot_b = getattr(self.model, 'rotation_b', 0) % 360
        offsets_b = rotated_offsets(rot_b)
        for i, (pin, leader) in enumerate(zip(self.anchor_b.pins, self.anchor_b.leaders)):
            color = color1 if i == 0 else color2
            pin.setBrush(QBrush(color))
            leader.setPen(QPen(color, 3, Qt.SolidLine))
            pin.setPos(offsets_b[i])
            leader.setLine(0, 0, offsets_b[i].x(), offsets_b[i].y())

        # Update helix geometry and colors
        self.helix.set_strand_colors(color1, color2)
        self.helix.update_geometry(self.anchor_a.pos(), self.anchor_b.pos())

    def set_signal(self, pin_item, wire_id, color):
        """
        Assign a wire ID to the given pin, update the model, and refresh layout/colors for both anchors.
        """
        # Determine anchor and index
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
        else:
            raise ValueError("Pin not found in anchors")

        # Update model
        if idx == 0:
            self.model.wire_id_1 = wire_id
        elif idx == 1:
            self.model.wire_id_2 = wire_id

        # Centralized color/layout update
        self.update_layout()

    def get_signal(self, pin_item):
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
        else:
            raise ValueError("Pin not found in anchors")
        if idx == 0:
            return self.model.wire_id_1
        elif idx == 1:
            return self.model.wire_id_2
        return None

    def boundingRect(self):
        # Use childrenBoundingRect to avoid rendering artifacts
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        pass  # No-op for now
