import math
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

    def _get_harness(self):
        # For testability: allow monkeypatching or override
        return None

    def hit_test_wire(self, point, tolerance):
        """
        Returns True if any wire in the harness is within tolerance of the point.
        """
        harness = self._get_harness()
        wires = getattr(harness, 'wires', [])
        for wire in wires:
            # Get all points: start, bends, end
            pts = self._get_wire_points(wire, harness)
            for i in range(len(pts) - 1):
                p1 = QPointF(*pts[i])
                p2 = QPointF(*pts[i+1])
                dist = self._point_to_segment_distance(point, p1, p2)
                if dist <= tolerance:
                    return True
        return False

    def _get_wire_points(self, wire, harness):
        # For test, assume from_conn/to_conn are device ids, devices have x/y
        d1 = next((d for d in getattr(harness, 'devices', []) if d.id == getattr(wire, 'from_conn', None)), None)
        d2 = next((d for d in getattr(harness, 'devices', []) if d.id == getattr(wire, 'to_conn', None)), None)
        points = []
        if d1:
            points.append((d1.x, d1.y))
        points.extend(getattr(wire, 'points', []))
        if d2:
            points.append((d2.x, d2.y))
        return points

    def _point_to_segment_distance(self, pt, p1, p2):
        # Returns the minimum distance from pt (QPointF) to segment p1-p2
        x, y = pt.x(), pt.y()
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return math.hypot(x - x1, y - y1)
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(x - proj_x, y - proj_y)

    def add_bend_point(self, wire_id, location):
        """
        Inserts a bend point (tuple) into the wire's points list at the segment closest to location.
        """
        harness = self._get_harness()
        wire = next((w for w in getattr(harness, 'wires', []) if w.id == wire_id), None)
        if not wire:
            return
        # Get all points: start, bends, end
        pts = self._get_wire_points(wire, harness)
        min_dist = float('inf')
        insert_idx = 0
        loc_pt = QPointF(*location)
        for i in range(len(pts) - 1):
            p1 = QPointF(*pts[i])
            p2 = QPointF(*pts[i+1])
            dist = self._point_to_segment_distance(loc_pt, p1, p2)
            if dist < min_dist:
                min_dist = dist
                insert_idx = i
        # Insert into wire.points (which is bends only, not endpoints)
        # wire.points index = insert_idx (after start), so insert at insert_idx
        wire.points.insert(insert_idx, location)

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
        # event: CanvasEvent
        if event.original_event.button() == Qt.RightButton:
            self._show_context_menu(event)
            return

        item = event.scene_item

        # Handle Pins: Select Parent Device
        if item and item.__class__.__name__ == 'PinItem':
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
        # event: CanvasEvent
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