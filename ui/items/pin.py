from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt
from ui.theme import ThemeManager
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin

class PinItem(ObservableGraphicsItemMixin, QGraphicsEllipseItem):
    __test_scenario__ = {
        'model_data': {'pin_id': 0, 'x': 0, 'y': 0},
        'expected_child_count': 0
    }
    def __init__(self, pin_model, parent=None):
        super().__init__(-0.5, -0.5, 1.0, 1.0, parent)
        self.setZValue(20)  # Pins above devices and wires
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