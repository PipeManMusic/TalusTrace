from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QPainterPath
from PySide6.QtCore import Qt
from ui.theme import ThemeManager

class PinItem(QGraphicsEllipseItem):
    def __init__(self, pin_model, parent=None):
        # A 1.0 unit circle centered at 0,0.
        # In World Space, this is exactly 1mm diameter.
        super().__init__(-0.5, -0.5, 1.0, 1.0, parent)
        
        self.pin = pin_model
        self.theme = ThemeManager()
        
        color = self.theme.get_color("pin_fill")
        self.setBrush(QBrush(color))
        self.setPen(Qt.NoPen)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    @property
    def model(self):
        return self.pin

    # ... (Hover methods remain standard) ...

    def shape(self):
        # Hitbox: 3mm diameter (1.5mm radius) for easier clicking
        path = QPainterPath()
        path.addEllipse(-1.5, -1.5, 3.0, 3.0)
        return path