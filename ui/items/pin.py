"""
Pin item for Talus Trace UI.

Provides a scene item for rendering and interacting with pins.
"""
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QBrush, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt
from ui.theme import ThemeManager
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin

class PinItem(ObservableGraphicsItemMixin, QGraphicsEllipseItem):
    """Scene item for rendering and interacting with a pin model."""
    __test_scenario__ = {
        'model_data': {'pin_id': 0, 'x': 0, 'y': 0},
        'expected_child_count': 0
    }
    def __init__(self, pin_model, parent=None):
        """Initialize PinItem with a pin model and optional parent."""
        # Make pin a small ellipse (8x8 px, centered)
        QGraphicsEllipseItem.__init__(self, -4, -4, 8, 8, parent)
        ObservableGraphicsItemMixin.__init__(self)
        self.setZValue(20)  # Pins above devices and wires
        self.pin = pin_model
        self.theme = ThemeManager()

        color = self.theme.get_color("pin_fill")
        outline = self.theme.get_color("pin_outline")
        if outline is None:
            outline = QColor("black")
        self.setBrush(QBrush(color))
        self.setPen(QPen(outline, 1.2))
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    @property
    def model(self):
        """Return the pin model associated with this item."""
        return self.pin

    # ... (rest of the visual logic)
    def shape(self):
        """Return the QPainterPath shape for the pin (for hit testing)."""
        path = QPainterPath()
        path.addEllipse(-1.5, -1.5, 3.0, 3.0)
        return path