from PySide6.QtCore import Qt
from tools.base import BaseTool
from core.selection import SelectionManager
from tools.move_tool import MoveTool as LogicMoveTool

class SelectTool(BaseTool):
    def __init__(self):
        self.dragging = False
        self.start_pos = None
        self.move_logic = LogicMoveTool()
        self.selection_manager = SelectionManager()

    def on_mouse_press(self, event):
        item = event.scene_item
        
        if item:
            # 1. Select the item in the core model
            self.selection_manager.set_selection([item.device])
            item.setSelected(True)
            
            # 2. Start the move transaction
            self.dragging = True
            self.start_pos = event.pos_mm
            self.move_logic.start(item.device)
        else:
            # Clicked empty space -> Deselect
            self.selection_manager.set_selection([])

    def on_mouse_move(self, event):
        if self.dragging and self.start_pos:
            current_pos = event.pos_mm
            dx = current_pos.x() - self.start_pos.x()
            dy = current_pos.y() - self.start_pos.y()
            
            # Update the logic (calculates new ghost position)
            self.move_logic.update(dx, dy)
            
            # Visual Feedback: Update the item position immediately
            if hasattr(event, 'scene_item') and event.scene_item:
                 event.scene_item.setPos(self.move_logic.ghost_item.x, self.move_logic.ghost_item.y)

    def on_mouse_release(self, event):
        if self.dragging:
            self.dragging = False
            # Commit the move to history (Undo/Redo)
            cmd = self.move_logic.commit()
            print(">> Move Committed")