from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QColor
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK

class PinItem(QGraphicsEllipseItem):
    def __init__(self, pin_model, parent=None):
        # 2x2 circle centered at 0,0 (radius 1)
        super().__init__(-1.0, -1.0, 2.0, 2.0, parent)
        self.pin = pin_model
        self.setBrush(QBrush(QColor(THEME_FALLBACK["pin_fill"])))
        self.setPen(Qt.NoPen)
        self.setAcceptHoverEvents(True)
        
        # Allow selection for Property Panel editing
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.cyan)) 
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Revert color based on selection state
        if self.isSelected():
            self.setBrush(QBrush(Qt.green))
        else:
            self.setBrush(QBrush(QColor(THEME_FALLBACK["pin_fill"])))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value: 
                self.setBrush(QBrush(Qt.green))
            else:
                self.setBrush(QBrush(QColor(THEME_FALLBACK["pin_fill"])))
        return super().itemChange(change, value)
