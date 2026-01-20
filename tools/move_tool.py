from PySide6.QtCore import Qt, QPointF
from tools.base_tool import BaseTool


class MoveCommand:
    """Undoable command for device move."""
    def __init__(self, device, old_pos, new_pos):
        self.device = device
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.executed = False

    def execute(self):
        self.device.x, self.device.y = self.new_pos
        self.executed = True

    def undo(self):
        self.device.x, self.device.y = self.old_pos

    def redo(self):
        self.execute()

    def mark_executed(self):
        self.executed = True

class MoveTool(BaseTool):
    __guide__ = {
        "name": "Move Tool",
        "description": "Drag items to move them.",
        "shortcuts": {}
    }

    def __init__(self):
        super().__init__()
        self.cursor = Qt.OpenHandCursor
        self.is_dragging = False
        self.start_pos = QPointF(0, 0)
        self.last_pos = QPointF(0, 0)
        self.target_override = None 
        self.ghost_item = None # Legacy test compatibility
        self.current_item = None

    def start(self, target=None, *args, **kwargs):
        """Called by ToolManager or Tests."""
        if target:
            self.target_override = target
            self.ghost_item = target # Alias for legacy tests
            self.is_dragging = True
            # Safely handle x/y as floats
            x = float(getattr(target, 'x', 0))
            y = float(getattr(target, 'y', 0))
            self.start_pos = QPointF(x, y)
            self.last_pos = self.start_pos
            self.cursor = Qt.ClosedHandCursor

    def update(self, dx=0, dy=0):
        """Legacy compatibility method for test_move_tool_ghosting."""
        if self.target_override:
            if hasattr(self.target_override, 'x'): self.target_override.x += dx
            if hasattr(self.target_override, 'y'): self.target_override.y += dy

    def on_mouse_press(self, event):
        # Only reset _move_command_pushed if not already dragging
        if not getattr(self, 'is_dragging', False):
            self._move_command_pushed = False
        print('[MoveTool] on_mouse_press called')
        btn = getattr(event, 'button', None)
        if btn is None and hasattr(event, 'original_event'):
            btn = event.original_event.button() if event.original_event else None
        if btn is not None and btn != Qt.LeftButton:
            print(f'[MoveTool] Ignoring non-left button: {btn}')
            return

        # Use event.scene_item as the drag target, but walk up parent chain if needed
        item = getattr(event, 'scene_item', None)
        pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
        # Walk up parent chain to find DeviceItem (has .model)
        original_item = item
        while item is not None and not hasattr(item, 'model'):
            parent = item.parentItem() if hasattr(item, 'parentItem') else None
            print(f"[MoveTool] Hit Item: {item}, Parent: {parent}")
            item = parent
        print(f'[MoveTool] Hit test: item={item}, type={type(item)}, pos={pos}')

        if item and hasattr(item, 'model'):
            print(f'[MoveTool] Valid item for drag: {item}, model id={getattr(item.model, "id", None)}')
            self.is_dragging = True
            self.start_pos = pos
            self.last_pos = pos
            self._drag_initial_pos = (float(getattr(item.model, 'x', 0)), float(getattr(item.model, 'y', 0)))
            self.cursor = Qt.ClosedHandCursor
            self.current_item = item
        else:
            print(f'[MoveTool] No valid item for drag, deselecting.')
            self.current_item = None
            if hasattr(self.api, 'deselect_all'):
                self.api.deselect_all()

    def on_mouse_move(self, event):
        print(f'[MoveTool] on_mouse_move called, is_dragging={self.is_dragging}')
        if not self.is_dragging:
            return

        pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        self.last_pos = pos

        # Real-time visual update: update model directly, do NOT push to undo stack
        if self.current_item and hasattr(self.current_item, 'model'):
            device = self.current_item.model
            device.x += dx
            device.y += dy
            # Also update the QGraphicsItem position directly for immediate feedback
            self.current_item.setPos(device.x, device.y)
        elif self.target_override:
            t = self.target_override
            if hasattr(t, 'x'): t.x += dx
            if hasattr(t, 'y'): t.y += dy

    def on_mouse_release(self, event):
        print(f'[MoveTool] on_mouse_release called, _move_command_pushed={getattr(self, "_move_command_pushed", None)}, is_dragging={self.is_dragging}')
        # Guard: if already pushed for this drag, do nothing
        if getattr(self, '_move_command_pushed', False):
            print('[MoveTool] on_mouse_release: already pushed, skipping')
            return
        if self.is_dragging:
            self.is_dragging = False
            self.cursor = Qt.OpenHandCursor

            pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
            self.last_pos = pos

            device = None
            old_pos = new_pos = None
            # Legacy/test path: target_override
            if self.target_override:
                device = self.target_override
                old_pos = getattr(self, '_drag_initial_pos', (self.start_pos.x(), self.start_pos.y()))
                # Calculate total delta and final position
                start_pos = self.start_pos
                initial_item_pos = getattr(self, '_drag_initial_pos', (start_pos.x(), start_pos.y()))
                total_dx = pos.x() - start_pos.x()
                total_dy = pos.y() - start_pos.y()
                final_pos = (initial_item_pos[0] + total_dx, initial_item_pos[1] + total_dy)
                # Update model to final position for visual sync
                if hasattr(device, 'x') and hasattr(device, 'y'):
                    device.x, device.y = final_pos
                new_pos = final_pos
            # Normal UI path: current_item
            elif self.current_item and hasattr(self.current_item, 'model'):
                device = self.current_item.model
                old_pos = getattr(self, '_drag_initial_pos', (self.start_pos.x(), self.start_pos.y()))
                start_pos = self.start_pos
                initial_item_pos = getattr(self, '_drag_initial_pos', (start_pos.x(), start_pos.y()))
                total_dx = pos.x() - start_pos.x()
                total_dy = pos.y() - start_pos.y()
                final_pos = (initial_item_pos[0] + total_dx, initial_item_pos[1] + total_dy)
                # Update model to final position for visual sync
                if hasattr(device, 'x') and hasattr(device, 'y'):
                    device.x, device.y = final_pos
                new_pos = final_pos

            # Only push if position changed and not already pushed
            if (
                hasattr(self.api.context, 'undo_stack')
                and device is not None
                and old_pos != new_pos
            ):
                print(f'[MoveTool] Pushing MoveCommand: {old_pos} -> {new_pos} for device {getattr(device, "id", None)}')
                from api.commands.move import MoveCommand
                self.api.context.undo_stack.push(MoveCommand(device, old_pos, new_pos))
                self._move_command_pushed = True

            self.target_override = None
            self.ghost_item = None
            if hasattr(self, '_drag_initial_pos'):
                del self._drag_initial_pos
            # Do not delete _move_command_pushed here; it is reset at the start of the next drag
            self.current_item = None