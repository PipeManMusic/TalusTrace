from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK

class PinItem(QGraphicsEllipseItem):
    def __init__(self, pin_model, parent=None):
        # Visual: 1.0mm Diameter Circle
        super().__init__(-0.5, -0.5, 1.0, 1.0, parent)
        self.pin = pin_model
        
        color = THEME_FALLBACK.get("pin_fill", "#FFFFFF")
        self.setBrush(QBrush(QColor(color)))
        self.setPen(Qt.NoPen)
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.cyan)) 
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.isSelected():
            self.setBrush(QBrush(Qt.green))
        else:
            color = THEME_FALLBACK.get("pin_fill", "#FFFFFF")
            self.setBrush(QBrush(QColor(color)))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value: 
                self.setBrush(QBrush(Qt.green))
            else:
                color = THEME_FALLBACK.get("pin_fill", "#FFFFFF")
                self.setBrush(QBrush(QColor(color)))
        return super().itemChange(change, value)

    def shape(self):
        # Hit Box: 3mm Diameter
        path = QPainterPath()
        path.addEllipse(-1.5, -1.5, 3.0, 3.0)
        return path