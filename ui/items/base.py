from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK

class SelectableItemMixin:
    """
    A Mixin that handles:
    1. Visual state updates (Hover/Select Halo).
    2. Common flags (Selectable/Movable).
    3. Model position updates (Dragging).
    """
    def init_mixin(self, model, is_ghost=False):
        self.model = model
        self.is_ghost = is_ghost
        
        # Standard Flags
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not self.is_ghost)
        self.setFlag(QGraphicsItem.ItemIsMovable, not self.is_ghost)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        if self.is_ghost:
            self.setAcceptedMouseButtons(Qt.NoButton)
            self.setZValue(2000)

        # Initial Visual State
        self.update_visual_state()

    def itemChange(self, change, value):
        """Centralized logic for UI updates."""
        
        # 1. Visual Updates (Blue Halo)
        if change == QGraphicsItem.ItemSelectedChange:
            # We do NOT update SelectionManager here. 
            # The Tool (SelectTool) is responsible for that.
            self.update_visual_state()

        # 2. Model Position Updates (Dragging)
        if change == QGraphicsItem.ItemPositionChange and hasattr(self, 'model'):
            # Only update if actually moving (value is QPointF)
            if hasattr(self.model, 'x') and hasattr(value, 'x'):
                self.model.x = value.x()
            if hasattr(self.model, 'y') and hasattr(value, 'y'):
                self.model.y = value.y()
            
        return super().itemChange(change, value)

    def update_visual_state(self):
        """Applies the standard 'Blue Glow' effect."""
        # We check isSelected() which is set by the Tool or Qt internals
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
        pass