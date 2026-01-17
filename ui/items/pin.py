from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt
from ui.theme import ThemeManager

class PinItem(QGraphicsEllipseItem):
    def __init__(self, pin_model, parent=None):
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

    # ... (rest of the visual logic)
    def shape(self):
        path = QPainterPath()
        path.addEllipse(-1.5, -1.5, 3.0, 3.0)
        return path