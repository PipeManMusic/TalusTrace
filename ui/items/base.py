"""
Base classes and mixins for custom QGraphicsItems in Talus Trace UI.

Provides shared logic for selection, event handling, and model association.
"""

from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QPointF

class SelectableItemMixin:
    """Mixin for QGraphicsItems to support selection and visual feedback."""
    def init_mixin(self, model, is_ghost=False):
        """Initialize the mixin with model and ghost status, setting flags and state."""
        self.model = model
        self.is_ghost = is_ghost
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not self.is_ghost)
        # Never allow native drag for real devices
        self.setFlag(QGraphicsItem.ItemIsMovable, self.is_ghost)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        if self.is_ghost:
            self.setAcceptedMouseButtons(Qt.NoButton)
            self.setZValue(2000)
        self.update_visual_state()


    def itemChange(self, change, value):
        """Custom itemChange handler for selection and grid snapping."""
        # Grid Snapping (in MM) for ghost items only
        if change == QGraphicsItem.ItemPositionChange and self.scene() and self.is_ghost:
            grid = 5.0 # Global grid setting
            new_pos = value
            x = round(new_pos.x() / grid) * grid
            y = round(new_pos.y() / grid) * grid
            return QPointF(x, y)

        if change == QGraphicsItem.ItemSelectedChange:
            # Prevent deselection on right-click (context menu)
            from PySide6.QtWidgets import QApplication
            mouse_event = QApplication.mouseButtons()
            is_right_click = mouse_event & Qt.RightButton
            if not value and is_right_click:
                # Ignore deselection if right-click is active
                return True
            self.update_visual_state()
            # NOTE: Selection state sync is handled exclusively by InputSystem -> API -> SelectionManager
            # The View does NOT drive selection; it only reflects it

        return super().itemChange(change, value)

    def update_visual_state(self):
        """Update the item's visual state based on selection and ghost status."""
        if self.isSelected() and not self.is_ghost:
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(15)
            effect.setColor(QColor(0, 200, 255))
            effect.setOffset(0, 0)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)
        self._apply_style()

    def _apply_style(self):
        """Apply custom style to the item (to be implemented by subclasses)."""
        pass