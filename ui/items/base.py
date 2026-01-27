"""
Base classes and mixins for custom QGraphicsItems in Talus Trace UI.

Provides shared logic for selection, event handling, and model association.
"""

from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QPointF

class SelectableItemMixin:
    """Mixin for QGraphicsItems to support selection, movement, and ghost logic."""
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
        """Custom itemChange handler for selection, movement, and grid snapping."""
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
            # Prevent deselection on right-click (context menu)
            from PySide6.QtWidgets import QApplication
            mouse_event = QApplication.mouseButtons()
            is_right_click = mouse_event & Qt.RightButton
            if not value and is_right_click:
                # Ignore deselection if right-click is active
                return True
            self.update_visual_state()
            try:
                from core.selection import SelectionManager
                manager = SelectionManager()
                # Sync selection to core manager when view selection toggles
                if value:
                    manager.select(getattr(self, 'model', None))
                else:
                    manager.clear_selection()
            except Exception:
                # Avoid breaking item selection if selection manager is unavailable
                pass
            # NOTE: Selection state sync is handled by InputSystem -> API -> SelectionManager
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