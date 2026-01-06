from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject
from PySide6.QtCore import QRectF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter
from talustrace.backend.models import TwistedPair

class TwistAnchorItem(QGraphicsItem):
    def __init__(self, pos, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.radius = 10
        self.setPos(*pos)
    def boundingRect(self):
        r = self.radius
        return QRectF(-r, -r, 2*r, 2*r)
    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor("orange")))
        painter.setPen(QPen(QColor("black")))
        painter.drawEllipse(self.boundingRect())

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
    def boundingRect(self):
        # Minimal bounding rect for QGraphicsObject
        return QRectF(0, 0, 1, 1)
    def paint(self, painter, option, widget=None):
        pass  # No-op for now
