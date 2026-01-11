from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK

class PinItem(QGraphicsEllipseItem):
    def __init__(self, pin_model, parent=None):
        # Visual: Small dot (radius 1.0 -> 2px diam)
        super().__init__(-1.0, -1.0, 2.0, 2.0, parent)
        self.pin = pin_model
        
        # Style
        color = THEME_FALLBACK.get("pin_fill", "#FFFFFF")
        self.setBrush(QBrush(QColor(color)))
        self.setPen(Qt.NoPen)
        
        # Interaction
        self.setAcceptHoverEvents(True)
        # Critical: Ensure this item catches clicks before the parent device does
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
        """
        Defines the 'Hit Box' for mouse clicks.
        We make this 12x12 (radius 6) so it's easy to grab,
        even though the visual dot is only 2x2.
        """
        path = QPainterPath()
        path.addEllipse(-6, -6, 12, 12)
        return path