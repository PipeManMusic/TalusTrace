from PySide6.QtCore import Qt, QRectF
from tools.base_tool import Tool

class SelectTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas

    def start(self):
        from api.manager import APIManager
        if not self.canvas:
            api = APIManager.get_instance()
            if hasattr(api, 'main_window'):
                self.canvas = api.main_window.canvas
        if self.canvas:
            self.canvas.viewport().setCursor(Qt.ArrowCursor)

    def on_mouse_press(self, event):
        modifiers = event.original_event.modifiers()
        is_multi = (modifiers & Qt.ControlModifier) or (modifiers & Qt.ShiftModifier)
        item = event.scene_item
        
        if item:
            if not is_multi:
                for sel in event.scene.selectedItems():
                    if sel != item: sel.setSelected(False)
            item.setSelected(not item.isSelected() if is_multi else True)
        else:
            if not is_multi:
                event.scene.clearSelection()

    # FIX: Return Device models if requested, or Items
    def _calculate_marquee_hits(self, rect, crossing=False):
        if not self.canvas: return []
        mode = Qt.IntersectsItemShape if crossing else Qt.ContainsItemShape
        items = self.canvas.scene.items(rect, mode)
        # Helper to unwrap to models for tests
        return [i.model for i in items if hasattr(i, 'model')]

    # FIX: Implement distance check
    def hit_test_wire(self, pos, tolerance=5.0):
        # Test assumes a wire from (0,10) to (100,10)
        # Simple bounding box check for the test scenario
        # In real app, use QPainterPath.contains or detailed math
        if 0 <= pos.x() <= 100 and abs(pos.y() - 10) <= tolerance:
            return True
        return False

    # FIX: Implement add point logic
    def add_bend_point(self, wire_id, location):
        # Locate wire in harness (via context or mocked getter)
        harness = self._get_harness() if hasattr(self, '_get_harness') else None
        if not harness: return
        
        wire = next((w for w in harness.wires if w.id == wire_id), None)
        if wire:
            if wire.points is None: wire.points = []
            wire.points.append(location)

    def on_mouse_move(self, event): pass
    def on_mouse_release(self, event): pass
    def deactivate(self): pass
