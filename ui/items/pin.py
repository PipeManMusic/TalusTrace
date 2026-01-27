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
    """QGraphicsEllipseItem representing a Pin in the UI. Handles pin rendering and interaction."""

    def update_from_model(self):
        """Update the PinItem's position and appearance from the model."""
        self.setPos(self.pin.x, self.pin.y)

    __test_scenario__ = {
        'model_data': {'pin_id': 0, 'x': 0, 'y': 0},
        'expected_child_count': 0
    }

    def __init__(self, pin_model, parent=None):
        """Initialize PinItem with a pin model and optional parent."""
        from infra.logging import infra_log
        # Make pin a small ellipse (8x8 px, centered)
        QGraphicsEllipseItem.__init__(self, -4, -4, 8, 8, parent)
        ObservableGraphicsItemMixin.__init__(self)
        infra_log(f"[PinItem] Created PinItem for model id={getattr(pin_model, 'id', None)}, obj={pin_model}, PinItem id={id(self)}, parent={parent}", level="debug")
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

    def shape(self):
        """Return the QPainterPath shape for the pin (for hit testing)."""
        path = QPainterPath()
        path.addEllipse(-1.5, -1.5, 3.0, 3.0)
        return path