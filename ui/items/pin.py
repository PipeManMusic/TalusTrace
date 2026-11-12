"""
Pin item for Talus Trace UI.

Provides a scene item for rendering and interacting with pins.
"""
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsDropShadowEffect
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
        from api.manager import APIManager
        # Read pin size from settings (default 5mm)
        try:
            size = APIManager.get_instance().settings.pin_size_mm
        except Exception:
            size = 5.0
        half = size / 2.0
        QGraphicsEllipseItem.__init__(self, -half, -half, size, size, parent)
        ObservableGraphicsItemMixin.__init__(self)
        self._pin_size = size
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

    def _apply_size(self):
        """Recompute the ellipse rect from the current pin_size_mm setting."""
        from api.manager import APIManager
        try:
            size = APIManager.get_instance().settings.pin_size_mm
        except Exception:
            size = 5.0
        self._pin_size = size
        half = size / 2.0
        self.setRect(-half, -half, size, size)
        self.update()

    @property
    def model(self):
        """Return the pin model associated with this item."""
        return self.pin

    def shape(self):
        """Return the QPainterPath shape for the pin (for hit testing)."""
        path = QPainterPath()
        s = getattr(self, '_pin_size', 5.0) * 0.6
        half = s / 2.0
        path.addEllipse(-half, -half, s, s)
        return path

    def itemChange(self, change, value):
        """Update visual state when selection changes."""
        if change == QGraphicsItem.ItemSelectedChange:
            # Defer visual update to after Qt applies the new state
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self._update_selection_visual)
        return super().itemChange(change, value)

    def _update_selection_visual(self):
        """Apply or remove glow effect based on selection state."""
        if self.isSelected():
            from ui.coordinates import THEME_FALLBACK
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(15)
            effect.setColor(QColor(THEME_FALLBACK["selection_glow"]))
            effect.setOffset(0, 0)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)