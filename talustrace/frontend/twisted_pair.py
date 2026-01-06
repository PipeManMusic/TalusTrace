from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsRectItem, QGraphicsPathItem
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath
from talustrace.backend.geometry import calculate_double_helix
from talustrace.backend.models import TwistedPair

class TwistAnchorItem(QGraphicsItem):
    def __init__(self, pos, parent=None, side=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.radius = 10
        self.setPos(*pos)
        self.side = side  # 'a' or 'b'
        # Create two pins and two leaders as children of the anchor
        self.pins = []
        self.leaders = []
        pin_colors = [QColor("green"), QColor("blue")]
        for i in range(2):
            pin = QGraphicsRectItem(-4, -4, 8, 8, self)
            pin.setBrush(QBrush(pin_colors[i]))
            self.pins.append(pin)
            leader = QGraphicsLineItem(self)
            leader.setPen(QPen(QColor("#888"), 1, Qt.DashLine))
            self.leaders.append(leader)

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
        return QRectF(-r, -r, 2*r, 2*r)

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor("orange")))
        painter.setPen(QPen(QColor("black")))
        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change in (QGraphicsItem.ItemPositionChange, QGraphicsItem.ItemPositionHasChanged):
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
        return self._rect

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.color1, 2))
        painter.drawPath(self.path1)
        painter.setPen(QPen(self.color2, 2))
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
        self.update_layout()


    def update_layout(self):
        """
        Update the pin and leader positions for both anchors based on the current
        anchor positions and their rotation values (from the model).
        Pin 1's offset is determined by rotation:
        - 0°: (0, 20)
        - 90°: (20, 0)
        - 180°: (0, -20)
        - 270°: (-20, 0)
        Pin 0 is always at (0, 0) local to the anchor.
        """
        def pin1_offset(rotation):
            rot = rotation % 360
            if rot == 0:
                return QPointF(0, 20)
            elif rot == 90:
                return QPointF(20, 0)
            elif rot == 180:
                return QPointF(0, -20)
            elif rot == 270:
                return QPointF(-20, 0)
            else:
                return QPointF(0, 20)

        # Snap anchor_a to grid for pins
        pos_a = self.anchor_a.scenePos()
        snap_a_x = round(pos_a.x() / 20) * 20
        snap_a_y = round(pos_a.y() / 20) * 20
        snap_origin_a = QPointF(snap_a_x, snap_a_y)
        rot_a = getattr(self.model, 'rotation_a', 0) % 360
        offsets_a = [QPointF(0, 0), pin1_offset(rot_a)]
        for i, (pin, leader) in enumerate(zip(self.anchor_a.pins, self.anchor_a.leaders)):
            snapped_scene = snap_origin_a + offsets_a[i]
            local = self.anchor_a.mapFromScene(snapped_scene)
            pin.setPos(local)
            leader.setLine(0, 0, local.x(), local.y())

        # Snap anchor_b to grid for pins
        pos_b = self.anchor_b.scenePos()
        snap_b_x = round(pos_b.x() / 20) * 20
        snap_b_y = round(pos_b.y() / 20) * 20
        snap_origin_b = QPointF(snap_b_x, snap_b_y)
        rot_b = getattr(self.model, 'rotation_b', 0) % 360
        offsets_b = [QPointF(0, 0), pin1_offset(rot_b)]
        for i, (pin, leader) in enumerate(zip(self.anchor_b.pins, self.anchor_b.leaders)):
            snapped_scene = snap_origin_b + offsets_b[i]
            local = self.anchor_b.mapFromScene(snapped_scene)
            pin.setPos(local)
            leader.setLine(0, 0, local.x(), local.y())

        # Update helix geometry
        self.helix.update_geometry(self.anchor_a.pos(), self.anchor_b.pos())

    def set_signal(self, pin_item, wire_id, color):
        """
        Assign a wire ID and color to the given pin, update the model,
        and propagate the color to the corresponding helix strand.
        Pin 0 sets strand 1, Pin 1 sets strand 2.
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

        # Update pin color
        from PySide6.QtGui import QColor, QBrush
        new_color = QColor(color) if not isinstance(color, QColor) else color
        pin_item.setBrush(QBrush(new_color))

        # Update helix strand colors
        c1 = self.helix.color1
        c2 = self.helix.color2
        if idx == 0:
            c1 = new_color
        elif idx == 1:
            c2 = new_color
        self.helix.set_strand_colors(c1, c2)

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
        # Minimal bounding rect for QGraphicsObject
        return QRectF(0, 0, 1, 1)

    def paint(self, painter, option, widget=None):
        pass  # No-op for now
