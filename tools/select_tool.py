from PySide6.QtCore import Qt, QPointF, QLineF
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction, QPainterPath
from tools.base import BaseTool
from core.selection import SelectionManager
from tools.move_tool import MoveTool as LogicMoveTool
from api.manager import APIManager
from core.twisted_pair import TwistedPair
from ui.items import PinItem, BundleItem
from core.wire import Wire

class SelectTool(BaseTool):

    def _calculate_marquee_hits(self, rect, crossing=False):
        """
        Returns a list of devices hit by the marquee selection.
        If crossing is False: only devices fully enclosed by rect are selected.
        If crossing is True: devices partially or fully intersecting rect are selected.
        """
        from PySide6.QtCore import QRectF
        harness = self._get_harness()
        hits = []
        for device in getattr(harness, 'devices', []):
            x = getattr(device, 'x', 0)
            y = getattr(device, 'y', 0)
            w = getattr(device, 'width', 20)
            h = getattr(device, 'height', 20)
            dev_rect = QRectF(x, y, w, h)
            if crossing:
                if rect.intersects(dev_rect):
                    hits.append(device)
            else:
                if rect.contains(dev_rect):
                    hits.append(device)
        return hits
        return hits

    def __init__(self):
        self.dragging = False
        self.start_pos = None
        self.move_logic = LogicMoveTool()
        self.selection_manager = SelectionManager()

    def on_mouse_press(self, event):
        if event.original_event.button() == Qt.RightButton:
            self._show_context_menu(event)
            return

        item = event.scene_item
        
        # Handle Pins: Select Parent Device
        if isinstance(item, PinItem):
            return

        # Handle Ghost/Unknown Items
        if item and not hasattr(item, 'device'):
            if item.parentItem() and hasattr(item.parentItem(), 'device'):
                item = item.parentItem()
            else:
                self.selection_manager.set_selection([])
                return

        if item and hasattr(item, 'device'):
            # Multi-select
            modifiers = event.original_event.modifiers()
            if modifiers & Qt.ControlModifier:
                current = set(self.selection_manager.selected_models)
                current.add(item.device)
                self.selection_manager.set_selection(list(current))
            else:
                self.selection_manager.set_selection([item.device])
            
            item.setSelected(True)
            self.dragging = True
            self.start_pos = event.pos_mm
            self.move_logic.start(item.device)
        else:
            self.selection_manager.set_selection([])

    def on_mouse_double_click(self, event):
        """
        Double Click on a Wire -> Add Elbow (Bend Point)
        """
        item = event.scene_item
        if isinstance(item, BundleItem):
            self._add_elbow(item, event.pos_mm)

    def _add_elbow(self, item: BundleItem, click_pos: QPointF):
        wire = item.device # BundleItem stores 'wire' model in 'device' attr
        if not isinstance(wire, Wire):
            return

        print(f">> Adding Elbow to {wire.id} at ({click_pos.x():.1f}, {click_pos.y():.1f})")

        # 1. Get current path points (Start -> Points -> End)
        # Note: BundleItem path_nodes includes start/end. Wire.points only stores intermediates.
        # We need to reconstruct the full list to find where to insert.
        # Ideally, we find the closest segment in item.path_nodes
        
        best_idx = 0
        min_dist = 999999.0
        
        nodes = item.path_nodes
        for i in range(len(nodes) - 1):
            p1 = QPointF(nodes[i][0], nodes[i][1])
            p2 = QPointF(nodes[i+1][0], nodes[i+1][1])
            line = QLineF(p1, p2)
            
            # Distance from click to this segment
            # (Simplified: center of segment check, or just insert based on index)
            # Real projection logic:
            # For prototype, we just append if empty, or insert.
            # Let's assume we insert at the end of the list for simplicity in Phase 5.0
            # A robust implementation projects point to line.
            pass

        # SIMPLE IMPLEMENTATION: Just append the point to the model
        # Real pathfinding logic will sort it out later.
        wire.points.append((click_pos.x(), click_pos.y()))
        
        # 2. Update Visuals
        # Re-construct path nodes: [Start] + [Points] + [End]
        # We need to know Start/End locations.
        # Hack: Read from existing item nodes[0] and nodes[-1]
        start_pt = nodes[0]
        end_pt = nodes[-1]
        
        new_nodes = [start_pt] + wire.points + [end_pt]
        
        # Update Item
        item.path_nodes = new_nodes
        
        qpath = QPainterPath()
        qpath.moveTo(new_nodes[0][0], new_nodes[0][1])
        for node in new_nodes[1:]:
            qpath.lineTo(node[0], node[1])
        item.setPath(qpath)

    def _show_context_menu(self, event):
        selection = self.selection_manager.selected_models
        menu = QMenu()
        
        from core.wire import Wire
        selected_wires = [obj for obj in selection if isinstance(obj, Wire)]
        
        if len(selected_wires) == 2:
            action = QAction("Twist Pair", menu)
            action.triggered.connect(lambda: self._create_twist(selected_wires))
            menu.addAction(action)
        
        if not menu.isEmpty():
            screen_pos = event.original_event.screenPos().toPoint()
            menu.exec(screen_pos)

    def _create_twist(self, wires):
        harness = APIManager.get_instance().context.harness
        new_pair = TwistedPair(
            id=f"TP-{len(harness.twisted_pairs)+1}",
            wire_ids=[w.id for w in wires]
        )
        harness.twisted_pairs.append(new_pair)
        self._visualize_twist(new_pair, wires)
        print(f">> Created Twisted Pair: {new_pair.id}")

    def _visualize_twist(self, pair, wires):
        pass # Visuals handled by TwistedPairItem later

    def on_mouse_move(self, event):
        if self.dragging and self.start_pos:
            current_pos = event.pos_mm
            dx = current_pos.x() - self.start_pos.x()
            dy = current_pos.y() - self.start_pos.y()
            self.move_logic.update(dx, dy)
            if hasattr(event, 'scene_item') and event.scene_item:
                 event.scene_item.setPos(self.move_logic.ghost_item.x, self.move_logic.ghost_item.y)

    def on_mouse_release(self, event):
        if self.dragging:
            self.dragging = False
            self.move_logic.commit()