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
        # Create leader and pin as children of the anchor
        self.leader = QGraphicsLineItem(self)
        self.leader.setPen(QPen(QColor("#888"), 1, Qt.DashLine))
        self.pin = QGraphicsRectItem(-4, -4, 8, 8, self)
        self.pin.setBrush(QBrush(QColor("blue")))

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
        # Expose pins and leaders for test compatibility
        self.pin_a = self.anchor_a.pin
        self.leader_a = self.anchor_a.leader
        self.pin_b = self.anchor_b.pin
        self.leader_b = self.anchor_b.leader
        self.pin_b.setBrush(QBrush(QColor("red")))
        self.update_layout()

    def update_layout(self):
        # Snap anchor_a to grid for pin_a
        pos_a = self.anchor_a.scenePos()
        snap_a_x = round(pos_a.x() / 20) * 20
        snap_a_y = round(pos_a.y() / 20) * 20
        snapped_a_scene = QPointF(snap_a_x, snap_a_y)
        local_a = self.anchor_a.mapFromScene(snapped_a_scene)
        self.pin_a.setPos(local_a)
        self.leader_a.setLine(0, 0, local_a.x(), local_a.y())

        # Snap anchor_b to grid for pin_b
        pos_b = self.anchor_b.scenePos()
        snap_b_x = round(pos_b.x() / 20) * 20
        snap_b_y = round(pos_b.y() / 20) * 20
        snapped_b_scene = QPointF(snap_b_x, snap_b_y)
        local_b = self.anchor_b.mapFromScene(snapped_b_scene)
        self.pin_b.setPos(local_b)
        self.leader_b.setLine(0, 0, local_b.x(), local_b.y())

    def boundingRect(self):
        # Minimal bounding rect for QGraphicsObject
        return QRectF(0, 0, 1, 1)

    def paint(self, painter, option, widget=None):
        pass  # No-op for now
