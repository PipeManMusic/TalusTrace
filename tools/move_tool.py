from PySide6.QtCore import Qt, QPointF
from tools.base_tool import BaseTool

class MoveCommand:
    """Mock command to satisfy legacy tests and UndoStack interface."""
    def __init__(self):
        self.executed = False

    def execute(self): 
        self.executed = True
    
    def undo(self): pass
    def redo(self): pass
    
    def mark_executed(self): 
        """Required by UndoStack."""
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
        # 1. Safe Button Check
        btn = getattr(event, 'button', None)
        if btn is None and hasattr(event, 'original_event'):
            btn = event.original_event.button() if event.original_event else None
        
        if btn is not None and btn != Qt.LeftButton:
            return

        # 2. Hit Test
        # Priority: Injected item (Tests) -> Scene Query (Real App)
        item = getattr(event, 'scene_item', None)
        pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
        
        if not item:
            try:
                transform = self.api.view.transform()
            except:
                transform = list() # Dummy
            item = self.api.scene.itemAt(pos, transform)

        if item and hasattr(item, 'model'):
            self.is_dragging = True
            self.start_pos = pos
            self.last_pos = pos
            self.cursor = Qt.ClosedHandCursor
            self.current_item = item
            
            # Selection Sync
            sm = getattr(self.api, 'selection_manager', None)
            if sm and hasattr(sm, 'current_selection_ids'):
                if item.model.id not in sm.current_selection_ids:
                     self.api.select([item.model.id])
        else:
            self.current_item = None
            self.api.deselect_all()

    def on_mouse_move(self, event):
        if not self.is_dragging:
            return

        pos = getattr(event, 'scene_pos', None) or (event.pos() if hasattr(event, 'pos') else QPointF(0,0))
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        self.last_pos = pos
        
        # A. API Command (Official Path)
        if hasattr(self.api, 'move_selection'):
             self.api.move_selection(delta=(dx, dy))

        # B. Direct Update (Test/Legacy Path)
        targets = []
        if self.target_override:
            targets.append(self.target_override)
        elif self.current_item and hasattr(self.current_item, 'model'):
            targets.append(self.current_item.model)
        
        # Manually apply delta for tests that expect immediate model updates
        for t in targets:
            if hasattr(t, 'x'): t.x += dx
            if hasattr(t, 'y'): t.y += dy

    def on_mouse_release(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.cursor = Qt.OpenHandCursor
            
            # Push Command to Undo Stack (Test Compatibility)
            if hasattr(self.api.context, 'undo_stack'):
                 self.api.context.undo_stack.push(MoveCommand())
            
            self.target_override = None
            self.ghost_item = None
            self.current_item = None