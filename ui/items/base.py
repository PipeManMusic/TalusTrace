from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QPointF

class SelectableItemMixin:
    def init_mixin(self, model, is_ghost=False):
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
        # Prevent non-ghost items from being moved by QGraphicsView drag unless MoveTool is handling the drag
        if not getattr(self, 'is_ghost', False):
            if change == QGraphicsItem.ItemPositionChange:
                try:
                    from api.manager import APIManager
                    api = APIManager.get_instance()
                    input_system = getattr(api, 'input_system', None)
                    move_tool = getattr(input_system, '_move_tool', None)
                    # Allow move if MoveTool is dragging (regardless of current_item)
                    if move_tool and getattr(move_tool, 'is_dragging', False):
                        pass  # Allow move
                    else:
                        return self.pos()  # Block move
                except Exception:
                    return self.pos()
            if change == QGraphicsItem.ItemPositionHasChanged:
                try:
                    from api.manager import APIManager
                    api = APIManager.get_instance()
                    input_system = getattr(api, 'input_system', None)
                    move_tool = getattr(input_system, '_move_tool', None)
                    if move_tool and getattr(move_tool, 'is_dragging', False):
                        pass  # Allow model sync
                    else:
                        return super().itemChange(change, value)
                except Exception:
                    return super().itemChange(change, value)

        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Grid Snapping (in MM) for ghost items only
            grid = 5.0 # Global grid setting
            new_pos = value
            x = round(new_pos.x() / grid) * grid
            y = round(new_pos.y() / grid) * grid
            return QPointF(x, y)

        if change == QGraphicsItem.ItemSelectedChange:
            self.update_visual_state()
            # Sync selection to core SelectionManager if selected
            try:
                from core.selection import SelectionManager
                if value:  # Selected
                    if hasattr(self, 'model'):
                        SelectionManager().select(self.model)
                else:  # Deselected
                    SelectionManager().clear_selection()
            except Exception:
                pass

        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, 'model'):
            # Model Update: Coordinates are already MM. Direct sync for ghost items only
            if getattr(self, 'is_ghost', False):
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