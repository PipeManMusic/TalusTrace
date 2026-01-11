from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QPointF

class SelectableItemMixin:
    def init_mixin(self, model, is_ghost=False):
        self.model = model
        self.is_ghost = is_ghost
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not self.is_ghost)
        self.setFlag(QGraphicsItem.ItemIsMovable, not self.is_ghost)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        if self.is_ghost:
            self.setAcceptedMouseButtons(Qt.NoButton)
            self.setZValue(2000)
        self.update_visual_state()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Grid Snapping (in MM)
            grid = 5.0 # Global grid setting
            new_pos = value
            x = round(new_pos.x() / grid) * grid
            y = round(new_pos.y() / grid) * grid
            return QPointF(x, y)

        if change == QGraphicsItem.ItemSelectedChange:
            self.update_visual_state()

        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, 'model'):
            # Model Update: Coordinates are already MM. Direct sync.
            try:
                if hasattr(self.model, 'x'): self.model.x = self.x()
                if hasattr(self.model, 'y'): self.model.y = self.y()
            except: pass
            
        return super().itemChange(change, value)

    def update_visual_state(self):
        if self.isSelected() and not self.is_ghost:
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(15)
            effect.setColor(QColor(0, 200, 255))
            effect.setOffset(0, 0)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)
        self._apply_style()

    def _apply_style(self): pass