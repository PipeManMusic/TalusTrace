from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtCore import Qt
from ui.coordinates import THEME_FALLBACK

class SelectableItemMixin:
    """
    A Mixin that handles:
    1. Synchronization with Core SelectionManager.
    2. Visual state updates (Hover/Select Halo).
    3. Common flags (Selectable/Movable).
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

        # Initial Sync with SelectionManager (Fixes Rotation/Undo Glitch)
        if not self.is_ghost and hasattr(self.model, 'id'):
            from core.selection import SelectionManager
            if self.model.id in SelectionManager().current_selection_ids:
                self.setSelected(True)

        self.update_visual_state()

    def itemChange(self, change, value):
        """Centralized logic for keeping UI and Core in sync."""
        if change == QGraphicsItem.ItemSelectedChange and hasattr(self, 'model'):
            from core.selection import SelectionManager
            mgr = SelectionManager()
            
            if value: # Selected
                mgr.current_selection_ids.add(self.model.id)
                if self.model not in mgr.selected_models:
                    mgr.selected_models.append(self.model)
            else: # Deselected
                mgr.current_selection_ids.discard(self.model.id)
                mgr.selected_models = [
                    m for m in mgr.selected_models 
                    if getattr(m, 'id', None) != self.model.id
                ]
            
            # Force immediate redraw to clear/add halo
            self.update_visual_state()
            self.update() 

        # Propagate position changes to model
        if change == QGraphicsItem.ItemPositionChange and hasattr(self, 'model'):
            if hasattr(self.model, 'x'): self.model.x = value.x()
            if hasattr(self.model, 'y'): self.model.y = value.y()
            
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

        # Hook for subclasses to apply specific styling (colors, pens)
        self._apply_style()

    def _apply_style(self):
        """Subclasses should override this to set Brush/Pen colors."""
        pass