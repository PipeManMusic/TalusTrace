from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsLineItem, QGraphicsRectItem
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter
from talustrace.backend.models import TwistedPair

class TwistAnchorItem(QGraphicsItem):
    def __init__(self, pos, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.radius = 10
        self.setPos(*pos)
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
    def boundingRect(self):
        return QRectF(0, 0, 1, 1)  # Placeholder
    def paint(self, painter, option, widget=None):
        pass  # No-op for now

class TwistedPairItem(QGraphicsObject):
    def __init__(self, model: TwistedPair, parent=None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.anchor_a = TwistAnchorItem(model.node_a, self)
        self.anchor_b = TwistAnchorItem(model.node_b, self)
        self.helix = DoubleHelixPathItem(self)
        self.update_layout()

    def update_layout(self):
        # Snap anchor_a to grid for pins
        pos_a = self.anchor_a.scenePos()
        snap_a_x = round(pos_a.x() / 20) * 20
        snap_a_y = round(pos_a.y() / 20) * 20
        snap_origin_a = QPointF(snap_a_x, snap_a_y)
        # Pin 0 at snap_origin, Pin 1 at snap_origin + (0, 20)
        for i, (pin, leader) in enumerate(zip(self.anchor_a.pins, self.anchor_a.leaders)):
            if i == 0:
                snapped_scene = snap_origin_a
            else:
                snapped_scene = snap_origin_a + QPointF(0, 20)
            local = self.anchor_a.mapFromScene(snapped_scene)
            pin.setPos(local)
            leader.setLine(0, 0, local.x(), local.y())

        # Snap anchor_b to grid for pins
        pos_b = self.anchor_b.scenePos()
        snap_b_x = round(pos_b.x() / 20) * 20
        snap_b_y = round(pos_b.y() / 20) * 20
        snap_origin_b = QPointF(snap_b_x, snap_b_y)
        for i, (pin, leader) in enumerate(zip(self.anchor_b.pins, self.anchor_b.leaders)):
            if i == 0:
                snapped_scene = snap_origin_b
            else:
                snapped_scene = snap_origin_b + QPointF(0, 20)
            local = self.anchor_b.mapFromScene(snapped_scene)
            pin.setPos(local)
            leader.setLine(0, 0, local.x(), local.y())

    def set_signal(self, pin_item, wire_id, color):
        # Determine anchor and index
        if pin_item in self.anchor_a.pins:
            idx = self.anchor_a.pins.index(pin_item)
        elif pin_item in self.anchor_b.pins:
            idx = self.anchor_b.pins.index(pin_item)
        else:
            raise ValueError("Pin not found in anchors")
        if idx == 0:
            self.model.wire_id_1 = wire_id
        elif idx == 1:
            self.model.wire_id_2 = wire_id
        # Optionally set color on pin
        pin_item.setBrush(QBrush(QColor(color)))

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
