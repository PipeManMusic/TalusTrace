"""
Pure rendering canvas for Talus Trace UI.

This canvas is a QGraphicsView subclass responsible ONLY for rendering the current model state.
It does not handle any input, selection, tool, or dispatcher logic. All such logic is managed by
dedicated managers (InputSystem, Dispatcher, SelectionManager, etc.).

Responsibilities:
  - Render devices, pins, wires, and other items from the model.
  - Update/redraw when notified of model changes.
  - Expose simple update/redraw methods (e.g., load_harness, zoom_extents).
  - Draw background grid.

All event handling, selection, and command logic must be routed through the appropriate manager.
The canvas is a pure view.
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from api.manager import APIManager

class HarnessCanvas(QGraphicsView):
    """Canvas view for displaying and interacting with harness items on the scene."""
    def dragEnterEvent(self, event):
        """Forward drag enter events to APIManager for contract compliance."""
        api = APIManager.get_instance()
        # Delegate acceptance decision to API - View does not parse mime formats
        if hasattr(api, 'handle_drag_enter'):
            accepted = api.handle_drag_enter(event)
            if accepted:
                self._ensure_drag_ghost(event)
                self._update_drag_ghost(event)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Keep the drag accepted while hovering so Qt delivers the drop.

        Qt only fires ``dropEvent`` if the widget continues to accept the
        proposed action during ``dragMoveEvent``.  Without this the library
        drag never completes and only double-click placement works.  While the
        drag is accepted we also move the ghost preview to follow the cursor.
        """
        api = APIManager.get_instance()
        if hasattr(api, 'handle_drag_enter'):
            if api.handle_drag_enter(event):
                self._ensure_drag_ghost(event)
                self._update_drag_ghost(event)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        """Remove the ghost preview when the drag leaves the canvas."""
        self._clear_drag_ghost()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """Forward drop events to APIManager for contract compliance."""
        self._clear_drag_ghost()
        api = APIManager.get_instance()
        if hasattr(api, 'handle_drop'):
            api.handle_drop(event)
        else:
            super().dropEvent(event)

    # ── Drag ghost preview ───────────────────────────────────────────
    def _drag_event_scene_pos(self, event):
        """Map a drag event's viewport position to scene coordinates."""
        if hasattr(event, 'position'):
            pt = event.position().toPoint()
        elif hasattr(event, 'pos'):
            pt = event.pos()
        else:
            from PySide6.QtCore import QPoint
            pt = QPoint(0, 0)
        return self.mapToScene(pt)

    def _ensure_drag_ghost(self, event):
        """Create the translucent ghost DeviceItem for the dragged part once."""
        if getattr(self, '_drag_ghost', None) is not None:
            return
        api = APIManager.get_instance()
        if not hasattr(api, 'make_drag_ghost_device'):
            return
        mime = event.mimeData() if hasattr(event, 'mimeData') else None
        text = mime.text() if mime and mime.hasText() else ""
        model = api.make_drag_ghost_device(text)
        if model is None:
            return
        from ui.items.device import DeviceItem
        ghost = DeviceItem(model, is_ghost=True)
        ghost.setZValue(2000)
        self.scene.addItem(ghost)
        self._drag_ghost = ghost

    def _update_drag_ghost(self, event):
        """Move the ghost to follow the cursor, snapped to the grid."""
        ghost = getattr(self, '_drag_ghost', None)
        if ghost is None:
            return
        scene_pos = self._drag_event_scene_pos(event)
        x, y = scene_pos.x(), scene_pos.y()
        api = APIManager.get_instance()
        if hasattr(api, 'settings') and hasattr(api.settings, 'snap'):
            x = api.settings.snap(x)
            y = api.settings.snap(y)
        try:
            ghost.setPos(x, y)
        except RuntimeError:
            self._drag_ghost = None

    def _clear_drag_ghost(self):
        """Remove the ghost preview from the scene, if present."""
        ghost = getattr(self, '_drag_ghost', None)
        if ghost is not None:
            try:
                self.scene.removeItem(ghost)
            except RuntimeError:
                pass
            self._drag_ghost = None

    def keyPressEvent(self, event):
        """Route Delete key to dispatcher for device/pin removal in headless tests."""
        if event.key() == Qt.Key_Delete:
            from api.actions import registry
            from core.device import Device
            from core.pin import Pin
            api = APIManager.get_instance()
            ctx = api.context
            
            # Set pin/device on context for delete handler
            selection_manager = getattr(ctx, 'selection_manager', None)
            if selection_manager and getattr(selection_manager, 'selected_models', None):
                selected_list = selection_manager.selected_models
                if selected_list:
                    selected = selected_list[0]
                    if isinstance(selected, Pin):
                        ctx.pin = selected
                        # Also find and set parent device
                        for dev in ctx.harness.devices:
                            if hasattr(dev, 'pins') and any(p.id == selected.id for p in dev.pins):
                                ctx.device = dev
                                break
                    elif isinstance(selected, Device):
                        ctx.device = selected
                        ctx.pin = None
            
            registry.execute("edit.delete", ctx)
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        """Zoom in/out on wheel scroll (contract compliance)."""
        # Standard zoom logic: scale view on wheel
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)
        event.accept()

    def contextMenuEvent(self, event):
        """Forward context menu events to APIManager for contract compliance."""
        api = APIManager.get_instance()
        if hasattr(api, 'open_context_menu'):
            # Detect item at the context menu event position
            item = None
            try:
                from PySide6.QtGui import QTransform
                scene_pos = self.mapToScene(event.pos())
                if self.scene:
                    item = self.scene.itemAt(scene_pos, QTransform())
            except Exception as e:
                import traceback
                traceback.print_exc()
            api.open_context_menu(event, item=item)
        else:
            super().contextMenuEvent(event)
    """
    Pure rendering canvas for Talus Trace. Only responsible for drawing the scene.
    All input, selection, and tool logic is handled elsewhere.
    """
    def __init__(self, parent=None):
        """Initialize the canvas with empty scene and configure rendering."""
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)

        # Enable drag-and-drop delivery.  Without setAcceptDrops(True) Qt never
        # routes dropEvent to this widget, so library drags silently fail and
        # only double-click placement works.  QAbstractScrollArea delivers drag
        # events to the *viewport* widget, and it only copies the view's
        # acceptDrops flag to the viewport at construction time (when it was
        # still False).  We must therefore set it on the viewport explicitly.
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

        # Ghost preview shown while a library part is dragged over the canvas.
        self._drag_ghost = None

        # Theme
        try:
            from ui.coordinates import THEME_FALLBACK
            self._theme = THEME_FALLBACK
        except Exception:
            self._theme = {"canvas_bg": "#121212", "grid_color": "#2d2d2d"}

        # Navigation
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # Visuals
        from PySide6.QtGui import QColor
        self.setBackgroundBrush(QColor(self._theme.get("canvas_bg", "#121212")))
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)

        # Subscribe to model_changed for device deletion
        api = APIManager.get_instance()
        # Subscribe to all API events for robust model sync
        if hasattr(api, 'subscribe_to_all'):
            api.subscribe_to_all(self._on_any_event)

    # ── Canonical action categories ──────────────────────────────────
    # Commands dispatch model_changed with many action strings.  The canvas
    # only needs four responses: reload the whole scene, add an item, remove
    # an item, or update an item in-place.  New tools/commands should use one
    # of the canonical names ("add", "remove", "update") when possible.  If
    # they invent a new action string, it will be auto-classified here—no
    # canvas edit required.
    _RELOAD_ACTIONS  = frozenset({"load", "new", "new_project", "restore_backup", "restore_autosave"})
    _ADD_ACTIONS     = frozenset({"add", "restore"})
    _REMOVE_ACTIONS  = frozenset({"remove", "delete"})
    # Everything with an item/items payload that isn't add/remove is an update.
    # Explicit membership is optional—unknown actions fall through to update.

    @classmethod
    def _classify_action(cls, action):
        """Map any model_changed action string to a canonical category.

        Returns one of: 'reload', 'add', 'remove', 'update', or None.
        Unknown actions that carry an item payload are treated as 'update'
        so future tools work without canvas changes.
        """
        if action in cls._RELOAD_ACTIONS:
            return "reload"
        if action in cls._ADD_ACTIONS:
            return "add"
        if action in cls._REMOVE_ACTIONS:
            return "remove"
        # Any other action with a payload is an update (safe default)
        return "update"

    def _on_any_event(self, event_type, data):
        """Handle any API event that could affect the canvas rendering."""
        if not hasattr(self, '_is_reloading'):
            self._is_reloading = False
        if self._is_reloading:
            return
        if event_type in ("undo", "redo"):
            try:
                self._is_reloading = True
                api = APIManager.get_instance()
                harness = getattr(api.context, 'harness', None)
                if harness is not None:
                    self.load_harness(harness)
            finally:
                self._is_reloading = False
        elif event_type == "model_changed":
            action = data.get("action") if isinstance(data, dict) else None
            category = self._classify_action(action)
            if category == "reload":
                try:
                    self._is_reloading = True
                    api = APIManager.get_instance()
                    harness = getattr(api.context, 'harness', None)
                    if harness is not None:
                        self.load_harness(harness)
                finally:
                    self._is_reloading = False
            else:
                self.on_model_changed(data, category)
        elif event_type == "bundle_added":
            self._handle_bundle_added(data)
        elif event_type == "bundle_removed":
            self._handle_bundle_removed(data)
        elif event_type == "bundle_updated":
            self._handle_bundle_updated(data)
        elif event_type == "selection_changed":
            self._sync_scene_selection(data)
        elif event_type == "settings_changed":
            from ui.items.pin import PinItem
            for item in self.scene.items():
                if isinstance(item, PinItem):
                    item._apply_size()
            self.viewport().update()

    def _sync_scene_selection(self, data):
        """Sync QGraphicsItem selection state to match the API SelectionManager."""
        selected_models = data.get("selection", []) if isinstance(data, dict) else []
        selected_ids = {getattr(m, 'id', None) for m in selected_models}
        selected_ids.discard(None)
        api = APIManager.get_instance()
        for item in self.scene.items():
            model = getattr(item, 'model', None)
            mid = getattr(model, 'id', None) if model else None
            if mid is None:
                continue
            should_be_selected = mid in selected_ids
            if item.isSelected() != should_be_selected:
                item.setSelected(should_be_selected)

    def on_model_changed(self, data, category=None):
        """Respond to model changes by updating or removing scene items as needed."""
        from api.manager import APIManager
        api = APIManager.get_instance()
        action = data.get("action") if isinstance(data, dict) else None
        item = data.get("item") if isinstance(data, dict) else None
        items = data.get("items") if isinstance(data, dict) else None
        if category is None:
            category = self._classify_action(action)

        if category == "remove" and item is not None:
            self._handle_remove(api, item)
        elif category == "add" and item is not None:
            self._handle_add(api, item)
        elif category == "update" and (item is not None or items is not None):
            self._handle_update(api, action, item, items)

    # ── Category handlers ─────────────────────────────────────────

    def _handle_remove(self, api, item):
        """Remove a scene item (and its grips) for a deleted model object."""
        model_id = getattr(item, "id", None)
        scene_item = api.get_scene_item(model_id)
        if scene_item is not None:
            if hasattr(scene_item, "setSelected"):
                scene_item.setSelected(False)
            if hasattr(scene_item, 'elbow_grips'):
                grips = list(scene_item.elbow_grips) + list(scene_item.segment_grips)
                scene_item.elbow_grips.clear()
                scene_item.segment_grips.clear()
                for g in grips:
                    s = g.scene()
                    if s:
                        s.removeItem(g)
            self.scene.removeItem(scene_item)
            api.unregister_scene_item(model_id)

    def _handle_add(self, api, item):
        """Create and register a scene item for a newly added model object."""
        model_id = getattr(item, "id", None)
        if not model_id or api.get_scene_item(model_id) is not None:
            return
        from core.pin import Pin
        if isinstance(item, Pin):
            parent_device_item = api.get_scene_item(getattr(item, "device_id", None))
            if parent_device_item is not None:
                from ui.items.pin import PinItem
                pin_item = PinItem(item, parent_device_item)
                pin_item.setPos(item.x, item.y)
                scene_ref = parent_device_item.scene() or self.scene
                if scene_ref is not None:
                    scene_ref.addItem(pin_item)
                api.register_scene_item(model_id, pin_item)
            return
        from core.wire import Wire
        if isinstance(item, Wire):
            from ui.items.wire import WireItem
            wire_item = WireItem(item)
            self.scene.addItem(wire_item)
            api.register_scene_item(model_id, wire_item)
            return
        from ui.items.device import DeviceItem
        device_item = DeviceItem(item)
        self.scene.addItem(device_item)
        api.register_scene_item(model_id, device_item)
        if hasattr(item, 'pins'):
            for pin in item.pins:
                pin_items = [child for child in device_item.childItems()
                           if hasattr(child, 'model') and hasattr(child.model, 'id')
                           and child.model.id == pin.id]
                if pin_items:
                    api.register_scene_item(pin.id, pin_items[0])

    def _handle_update(self, api, action, item, items):
        """Update scene items to reflect model property changes."""
        update_targets = items if items is not None else [item]
        for target in update_targets:
            model_id = getattr(target, "id", None)
            scene_item = api.get_scene_item(model_id)
            if scene_item is not None:
                if hasattr(scene_item, 'update_from_model'):
                    scene_item.update_from_model()
                else:
                    if hasattr(target, 'x') and hasattr(target, 'y'):
                        scene_item.setPos(target.x, target.y)
                    if hasattr(target, 'rotation') and hasattr(scene_item, 'rotation'):
                        scene_item.setRotation(target.rotation)
            api._update_connected_wires(target)

    # ── Bundle rendering ─────────────────────────────────────────

    def _wire_lookup(self):
        """Return a ``wire_id -> Wire`` map for the current harness."""
        api = APIManager.get_instance()
        harness = getattr(api.context, 'harness', None)
        wires = getattr(harness, 'wires', []) if harness is not None else []
        return {getattr(w, 'id', None): w for w in wires}

    def _handle_bundle_added(self, bundle):
        """Create and register a BundleItem for a newly emerged bundle."""
        api = APIManager.get_instance()
        model_id = getattr(bundle, "id", None)
        if not model_id or api.get_scene_item(model_id) is not None:
            return
        from ui.items.bundle import BundleItem
        item = BundleItem(bundle, self._wire_lookup())
        self.scene.addItem(item)
        api.register_scene_item(model_id, item)

    def _handle_bundle_removed(self, bundle):
        """Remove the BundleItem for a bundle that no longer exists."""
        api = APIManager.get_instance()
        model_id = getattr(bundle, "id", None)
        scene_item = api.get_scene_item(model_id) if model_id else None
        if scene_item is not None:
            self.scene.removeItem(scene_item)
            api.unregister_scene_item(model_id)

    def _handle_bundle_updated(self, bundle):
        """Refresh an existing BundleItem's trunk/breakouts after a layout change."""
        api = APIManager.get_instance()
        model_id = getattr(bundle, "id", None)
        scene_item = api.get_scene_item(model_id) if model_id else None
        if scene_item is not None and hasattr(scene_item, 'update_from_model'):
            scene_item.update_from_model(bundle, self._wire_lookup())

    def drawBackground(self, painter, rect):
        """Draw the background grid with minor and major lines."""
        import math
        super().drawBackground(painter, rect)
        from PySide6.QtGui import QColor, QPen
        from PySide6.QtCore import QLineF

        grid_size = 2.54
        try:
            from api.manager import APIManager
            api = APIManager.get_instance()
            grid_size = max(getattr(api.settings, 'grid_size_mm', 2.54), 0.5)
        except Exception:
            pass

        major_every = 10  # every Nth minor line is a major line
        base_color = QColor(self._theme.get("grid_color", "#2d2d2d"))

        # Minor grid pen — faint dots
        minor_color = QColor(base_color)
        minor_color.setAlpha(50)
        minor_pen = QPen(minor_color, 0)

        # Major grid pen — more visible
        major_color = QColor(base_color)
        major_color.setAlpha(140)
        major_pen = QPen(major_color, 0)

        left = rect.left()
        top = rect.top()
        right = rect.right()
        bottom = rect.bottom()

        # Align start to grid
        start_x = math.floor(left / grid_size) * grid_size
        start_y = math.floor(top / grid_size) * grid_size

        # Draw vertical lines
        minor_lines = []
        major_lines = []
        ix = 0
        x = start_x
        while x <= right:
            line = QLineF(x, top, x, bottom)
            if ix % major_every == 0:
                major_lines.append(line)
            else:
                minor_lines.append(line)
            x += grid_size
            ix += 1

        # Draw horizontal lines
        iy = 0
        y = start_y
        while y <= bottom:
            line = QLineF(left, y, right, y)
            if iy % major_every == 0:
                major_lines.append(line)
            else:
                minor_lines.append(line)
            y += grid_size
            iy += 1

        painter.setPen(minor_pen)
        painter.drawLines(minor_lines)
        painter.setPen(major_pen)
        painter.drawLines(major_lines)

    def load_harness(self, harness):
        """Populate the scene with items from the harness model (devices and wires)."""
        self.scene.clear()
        api = APIManager.get_instance()
        # Devices
        from ui.items.device import DeviceItem
        for dev in getattr(harness, 'devices', []):
            item = DeviceItem(dev)
            self.scene.addItem(item)
            api.register_scene_item(dev.id, item)
            # Register PinItems created by DeviceItem
            if hasattr(dev, 'pins'):
                for pin in dev.pins:
                    pin_items = [child for child in item.childItems() 
                               if hasattr(child, 'model') and hasattr(child.model, 'id') 
                               and child.model.id == pin.id]
                    if pin_items:
                        api.register_scene_item(pin.id, pin_items[0])
        # Wires
        from ui.items.wire import WireItem
        for wire in getattr(harness, 'wires', []):
            item = WireItem(wire)
            self.scene.addItem(item)
            api.register_scene_item(wire.id, item)
        # Bundles (emergent trunk lines under the wires)
        from infra.bundle_inference import BUNDLING_ENABLED
        if BUNDLING_ENABLED:
            from ui.items.bundle import BundleItem
            wire_lookup = {getattr(w, 'id', None): w for w in getattr(harness, 'wires', [])}
            for bundle in getattr(harness, 'bundles', []):
                item = BundleItem(bundle, wire_lookup)
                self.scene.addItem(item)
                api.register_scene_item(bundle.id, item)

    def zoom_extents(self):
        """Zoom the view to fit all items in the scene with padding."""
        rect = self.scene.itemsBoundingRect()
        if rect.isNull(): return
        pad = max(rect.width(), rect.height()) * 0.1
        rect.adjust(-pad, -pad, pad, pad)
        self.fitInView(rect, Qt.KeepAspectRatio)