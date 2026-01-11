from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtCore import Qt, QPointF
from ui.coordinates import THEME_FALLBACK

class SelectableItemMixin:
    """
    A Mixin that handles:
    1. Visual state updates (Hover/Select Halo).
    2. Common flags (Selectable/Movable).
    3. Model position updates (Dragging).
    4. GRID SNAPPING (New)
    """
    def init_mixin(self, model, is_ghost=False):
        self.model = model
        self.is_ghost = is_ghost
        
        # Standard Flags
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not self.is_ghost)
        
        # We keep ItemIsMovable True so you can drag with Select Tool,
        # but we constrain it in itemChange.
        self.setFlag(QGraphicsItem.ItemIsMovable, not self.is_ghost)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        if self.is_ghost:
            self.setAcceptedMouseButtons(Qt.NoButton)
            self.setZValue(2000)

        # Initial Visual State
        self.update_visual_state()

    def itemChange(self, change, value):
        """Centralized logic for UI updates and Constraints."""
        
        # --- 1. FORCE GRID SNAPPING ---
        # This intercepts Qt's internal move logic and forces the result to the grid.
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Lazy load API to avoid circular imports
            from api.manager import APIManager
            try:
                transformer = APIManager.get_instance().transformer
                new_pos = value # value is a QPointF
                
                # Snap the proposed position
                x = transformer.snap_to_grid(new_pos.x())
                y = transformer.snap_to_grid(new_pos.y())
                
                return QPointF(x, y)
            except:
                # Fallback if API isn't ready (shouldn't happen in runtime)
                pass

        # --- 2. Visual Updates (Blue Halo) ---
        if change == QGraphicsItem.ItemSelectedChange:
            self.update_visual_state()

        # --- 3. Model Sync (Dragging) ---
        # Note: We check ItemPositionHasChanged to update the model AFTER the snap
        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, 'model'):
            # Update the underlying data model to match the snapped UI position
            if hasattr(self.model, 'x'):
                self.model.x = self.x()
            if hasattr(self.model, 'y'):
                self.model.y = self.y()
            
        return super().itemChange(change, value)

    def update_visual_state(self):
        """Applies the standard 'Blue Glow' effect."""
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