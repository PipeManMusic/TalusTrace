"""
Input System for Talus Trace (PH5-INPUT.1)

Design:
The input system is a pure event router. It receives all user input events (mouse, keyboard, tablet, etc.) and delegates them to the appropriate tool, dispatcher, or context menu manager. It does NOT manage selection or perform any direct state changes itself. All selection, model mutation, and contract enforcement are handled by the dispatcher, APIManager, or selection manager. The input system ensures that all input is routed to the correct handler, and that UI-to-infra contracts are strictly enforced. This design decouples input routing from business logic, making the system robust, testable, and maintainable.
"""

import logging
def _log_input_event(event_name, **kwargs):
    """Log input system events for debugging."""
    logging.debug(f"[INPUT_SYSTEM][EVENT] {event_name} | " + ", ".join(f"{k}={v}" for k, v in kwargs.items()))

import yaml
import os
from PySide6.QtCore import QObject, QEvent, Qt
from api.actions import registry

class InputSystem(QObject):
    """System for managing and routing input events to appropriate tools and handlers."""
    def __init__(self, config_path=None, move_tool=None):
        """Initialize the input system with optional configuration and tool."""
        logging.debug(f"[INPUT_SYSTEM][INIT] config_path={config_path}, move_tool={move_tool}")
        super().__init__()
        self.canvas = None
        self.config_path = config_path
        self.global_keymap = {}  # {Qt.Key or (Qt.Key, modifier): action_id}
        self._move_tool = move_tool  # Allow dependency injection for tests
        # Register edit.delete action (avoids circular import)
        import api.edit_delete_action
        # 1. Load Defaults (Safety Net)
        self._load_defaults()
        # 2. Override with Config if available
        if self.config_path:
            self._load_keymap()

    def register_shortcut(self, key, action_id):
        """Register a shortcut mapping (key: Qt.Key or str, action_id: str)."""
        if isinstance(key, str):
            qt_key = getattr(Qt, f"Key_{key.upper()}", None)
            if qt_key is not None:
                self.global_keymap[qt_key] = action_id
        else:
            self.global_keymap[key] = action_id

    def _load_defaults(self):
        """Ensure critical shortcuts work out-of-the-box."""
        self.global_keymap[(Qt.Key_Z, Qt.ControlModifier)] = "edit.undo"
        self.global_keymap[(Qt.Key_Y, Qt.ControlModifier)] = "edit.redo"
        self.global_keymap[(Qt.Key_N, Qt.ControlModifier)] = "file.new"
        self.global_keymap[(Qt.Key_O, Qt.ControlModifier)] = "file.open"
        self.global_keymap[(Qt.Key_S, Qt.ControlModifier)] = "file.save"
        self.global_keymap[(Qt.Key_Q, Qt.ControlModifier)] = "file.exit"
        self.global_keymap[Qt.Key_Delete] = "edit.delete"
        self.global_keymap[Qt.Key_R] = "edit.rotate_cw"

    @property
    def api(self):
        """Return the singleton APIManager instance."""
        from api.manager import APIManager
        return APIManager.get_instance()
    def install(self, target):
        """
        Connect the InputSystem as an event filter.
        Always install on the QGraphicsView's viewport for robust mouse event handling.
        Accepts either the canvas (QGraphicsView) or its viewport.
        """
        logging.debug(f"[INPUT_SYSTEM][INSTALL] Installing event filter on: {target}")
        # If target is the viewport, set self.canvas to its parent (the QGraphicsView)
        if hasattr(target, 'parent') and hasattr(target.parent(), 'mapToScene'):
            self.canvas = target.parent()
        else:
            self.canvas = target
        if hasattr(target, 'installEventFilter'):
            target.installEventFilter(self)

    def handle_canvas_event(self, event):
        """Route mouse events from the Canvas to the active tool or injected MoveTool."""
        etype = event.original_event.type()
        scene_pos = getattr(event, 'scene_pos', None)

        # Fast path: active drag in progress — skip all hit-testing and selection queries
        active_drag = getattr(self, '_active_drag_tool', None)
        if active_drag is not None:
            if etype == QEvent.MouseMove and hasattr(active_drag, 'update_drag'):
                active_drag.update_drag(scene_pos)
                return True
            if etype == QEvent.MouseButtonRelease and hasattr(active_drag, 'finish_drag'):
                active_drag.finish_drag(scene_pos)
                self._active_drag_tool = None
                return True

        tool = self._move_tool if self._move_tool is not None else self.api.tool_manager.active_tool
        # Use API facade instead of direct Core access
        selection_ids = self.api.get_selection()
        is_move_tool = tool.__class__.__name__ == "MoveTool"
        item = getattr(event, 'scene_item', None) or getattr(event, 'item_at', None)
        # If item is still None and we have a main_window with canvas, query the scene directly
        if item is None and scene_pos is not None:
            try:
                if hasattr(self.api, 'main_window') and hasattr(self.api.main_window, 'canvas'):
                    canvas = self.api.main_window.canvas
                    if canvas and hasattr(canvas, 'scene'):
                        from PySide6.QtGui import QTransform
                        scene = canvas.scene
                        if scene:
                            item = scene.itemAt(scene_pos, QTransform())
            except Exception as e:
                logging.warning(f"[InputSystem.handle_canvas_event] Failed to get item at scene position: {e}")
                item = None
        logging.debug(f"[InputSystem.handle_canvas_event] CALLED: etype={etype}, tool={tool}, selection_ids={selection_ids}, scene_pos={scene_pos}, item={item}")

        # Double-click on a pin starts a wire
        if etype == QEvent.MouseButtonDblClick:
            from ui.items.pin import PinItem
            from ui.items.wire import WireItem
            if isinstance(item, PinItem) and hasattr(item, 'pin'):
                device_item = item.parentItem()
                if device_item and hasattr(device_item, 'model'):
                    wire_tool = self.api.tool_manager.get_tool('wire')
                    if wire_tool:
                        self.api.tool_manager.set_tool('wire')
                        wire_tool.begin_wire_from_pin(item.pin, device_item.model, scene_pos)
                        return True
            elif isinstance(item, WireItem) and hasattr(item, 'model'):
                wire_model = item.model
                nodes = getattr(wire_model, 'path_nodes', [])
                if nodes and len(nodes) >= 2:
                    # Find the segment closest to the click and insert an elbow there
                    best_idx = 1
                    best_dist = float('inf')
                    sx, sy = scene_pos.x(), scene_pos.y()
                    for i in range(len(nodes) - 1):
                        ax, ay = nodes[i][0], nodes[i][1]
                        bx, by = nodes[i + 1][0], nodes[i + 1][1]
                        # Distance from point to line segment
                        dx, dy = bx - ax, by - ay
                        seg_len_sq = dx * dx + dy * dy
                        if seg_len_sq == 0:
                            t = 0
                        else:
                            t = max(0, min(1, ((sx - ax) * dx + (sy - ay) * dy) / seg_len_sq))
                        px, py = ax + t * dx, ay + t * dy
                        dist = ((sx - px) ** 2 + (sy - py) ** 2) ** 0.5
                        if dist < best_dist:
                            best_dist = dist
                            best_idx = i + 1
                    # Snap elbow position to grid
                    if hasattr(self.api, 'settings') and hasattr(self.api.settings, 'snap'):
                        sx = self.api.settings.snap(sx)
                        sy = self.api.settings.snap(sy)
                    self.api.add_elbow(wire_model, best_idx, [sx, sy])
                    return True
            return True  # Consume other double-clicks
        # 1. Right Click Handling (Context Menu)
        if etype == QEvent.MouseButtonPress:
            btn_val = event.button() if hasattr(event, 'button') and callable(event.button) else getattr(event, 'button', None)
            orig_btn_val = event.original_event.button() if hasattr(event.original_event, 'button') and callable(event.original_event.button) else getattr(event.original_event, 'button', None)
            logging.debug(f"[INPUT_SYSTEM][MOUSE_PRESS] event.button={btn_val} (type={type(btn_val)}), orig_event.button={orig_btn_val} (type={type(orig_btn_val)}) Qt.RightButton={Qt.RightButton}")
            is_right_click = btn_val == Qt.RightButton or orig_btn_val == Qt.RightButton
            if is_right_click:
                # Select the right-clicked item so context menu commands apply to it
                if item is not None and hasattr(item, 'model'):
                    model_id = getattr(item.model, 'id', None)
                    if model_id:
                        self.api.select([model_id])
                # NOTE: Use the item we detected above from scene.itemAt(), don't overwrite it
                logging.debug(f"[INPUT_SYSTEM][RIGHT_CLICK DETECTED] item={item} type={type(item)} id={id(item) if item else None}, calling open_context_menu if available.")
                # Extra diagnostics for context menu contract
                from ui.items.device import DeviceItem
                from ui.items.pin import PinItem
                from ui.items.wire import WireItem
                # Log full type chain for item
                import inspect
                item_type = None
                if item is not None:
                    mro = inspect.getmro(type(item))
                    item_type = [cls.__name__ for cls in mro]
                logging.debug(f"[INPUT_SYSTEM][CONTEXT_MENU] item_type_chain={item_type}, item_id={getattr(item, 'id', None)}, item_model_id={getattr(getattr(item, 'model', None), 'id', None)}")
                # Fallback: forcibly resolve PinItem if model has 'device_id' and 'id'
                if item is not None and hasattr(item, 'model') and hasattr(item.model, 'device_id') and hasattr(item.model, 'id'):
                    logging.debug(f"[INPUT_SYSTEM][CONTEXT_MENU] Forcing PinItem menu_type for item with device_id and id.")
                if hasattr(self.api, 'open_context_menu'):
                    logging.debug(f"[INPUT_SYSTEM][CALL] open_context_menu(event={event.original_event}, item={item})")
                    import inspect
                    type_chain = [cls.__name__ for cls in inspect.getmro(type(item))] if item is not None else []
                    logging.debug(f"[TRACE][InputSystem] open_context_menu CALLED: item={repr(item)}, id={id(item)}, type={type(item)}, type_chain={type_chain}")
                    if item is not None:
                        self.api.open_context_menu(event.original_event, item=item)
                    else:
                        self.api.open_context_menu(event.original_event)
                else:
                    logging.debug(f"[INPUT_SYSTEM][NO OPEN_CONTEXT_MENU] api={self.api}")
                # Do NOT forward right-click to the active tool after context menu;
                # the menu has already been handled and the item may have been deleted.
                return True
        # Populate scene_item on the event so tools can use the already-resolved item
        if item is not None:
            event.scene_item = item
        # 2. Tool Handling
        if tool:
            if etype == QEvent.MouseButtonPress:
                logging.debug(f"[INPUT_SYSTEM][MOUSE_PRESS] tool={tool}, item={item}")
                btn_val = event.button() if hasattr(event, 'button') and callable(event.button) else getattr(event, 'button', None)
                is_left = btn_val == Qt.LeftButton
                # Resolve drag tool: if the active tool supports drag, use it directly.
                # Otherwise, on left-click with an item, grab the registered MoveTool.
                # Skip drag initiation if the active tool handles its own clicks
                # (e.g. WireTool clicking on pins to complete a wire).
                drag_tool = None
                tool_handles_own_clicks = tool.__class__.__name__ in ("WireTool", "PlacementTool")
                from ui.items.wire import WireItem
                item_is_draggable = item is not None and hasattr(item, 'model') and not isinstance(item, WireItem)
                if item_is_draggable and not tool_handles_own_clicks:
                    if hasattr(tool, 'start_drag'):
                        drag_tool = tool
                    elif is_left:
                        drag_tool = self.api.tool_manager.get_tool("move")
                if drag_tool and hasattr(drag_tool, 'start_drag'):
                    model_id = getattr(item.model, 'id', None)
                    if model_id and model_id not in (selection_ids or []):
                        self.api.select([model_id], tool_name="move")
                    drag_tool.start_drag(item, scene_pos)
                    self._active_drag_tool = drag_tool
                    return True  # Consume event so Qt doesn't interfere
                # Interactive grip items (elbow/segment grips) handle their
                # own mouse events.  Do NOT route to the tool — that would
                # trigger deselect_all and destroy the grips mid-click.
                if item is not None and getattr(item, '_interactive_grip', False):
                    return False
                # Only forward on_mouse_press to the active tool if we didn't
                # start a drag via a different tool (e.g. MoveTool while SelectTool
                # is active).  If the active tool IS the drag tool, let it handle both.
                if drag_tool is None or drag_tool is tool:
                    if hasattr(tool, 'on_mouse_press'):
                        logging.debug(f"[InputSystem.handle_canvas_event] Calling tool.on_mouse_press for tool={tool}")
                        tool.on_mouse_press(event)
            elif etype == QEvent.MouseMove:
                if hasattr(tool, 'on_mouse_move'):
                    tool.on_mouse_move(event)
            elif etype == QEvent.MouseButtonRelease:
                self._active_drag_tool = None
                if hasattr(tool, 'on_mouse_release'):
                    tool.on_mouse_release(event)
        return False

    def eventFilter(self, obj, event):
        """
        InputSystem event filter for mouse/keyboard events.
        Always install this on the QGraphicsView's viewport for robust mouse event handling.
        This method will resolve the parent QGraphicsView for coordinate mapping.
        """
        logging.debug(f"[InputSystem.eventFilter] CALLED: type={event.type()}")
        if event.type() == QEvent.KeyPress:
            if self._handle_key(event):
                return True

        # Middle-button pan: handle directly, bypass tool routing
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()
            if self.canvas:
                self.canvas.setCursor(Qt.ClosedHandCursor)
            return True
        if event.type() == QEvent.MouseMove and getattr(self, '_is_panning', False):
            pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()
            delta = pos - self._pan_start
            self._pan_start = pos
            if self.canvas:
                self.canvas.horizontalScrollBar().setValue(
                    self.canvas.horizontalScrollBar().value() - delta.x())
                self.canvas.verticalScrollBar().setValue(
                    self.canvas.verticalScrollBar().value() - delta.y())
            return True
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.MiddleButton:
            self._is_panning = False
            if self.canvas:
                self.canvas.setCursor(Qt.ArrowCursor)
            return True

        # Route mouse and context menu events to handle_canvas_event
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseMove, QEvent.ContextMenu, QEvent.MouseButtonDblClick):
            from PySide6.QtCore import QPoint
            # Find the QGraphicsView (canvas) for coordinate mapping
            view = obj
            if not hasattr(view, 'mapToScene'):
                # obj is likely the viewport; get its parent QGraphicsView
                view = obj.parent()
            class CanvasEvent:
                """Wrapper for canvas input events with scene context."""
                def __init__(self, original_event):
                    """Initialize a canvas event with the original Qt event."""
                    self.original_event = original_event
                    # Extract button value by calling the method if callable
                    if hasattr(original_event, 'button') and callable(original_event.button):
                        self.button = original_event.button()
                    else:
                        self.button = getattr(original_event, 'button', None)
                    # Get scene position as QPointF
                    if hasattr(original_event, 'position'):
                        pos = original_event.position().toPoint()
                    else:
                        pos = original_event.pos()
                    scene_posf = view.mapToScene(pos)
                    self.scene_pos = scene_posf
                    # Let the canvas/scene determine the item - don't query here
                    self.scene_item = None
            logging.debug(f"[InputSystem.eventFilter] Creating CanvasEvent for event: {event}")
            canvas_event = CanvasEvent(event)
            return self.handle_canvas_event(canvas_event)
            # Do not block event propagation
            return False
        return super().eventFilter(obj, event)

    def _handle_key(self, event):
        """Handle a key event, executing mapped actions or shortcuts if present."""
        key = event.key()
        modifiers = event.modifiers()
        logging.debug(f"[INPUT_SYSTEM][_HANDLE_KEY] key={key}, modifiers={modifiers}")

        # Escape: cancel active tool and return to select tool
        if key == Qt.Key_Escape:
            tool = self.api.tool_manager.active_tool
            if hasattr(tool, 'deactivate'):
                tool.deactivate()
            self.api.tool_manager.set_tool('select')
            return True

        # 1. Check modifier combos from keymap (e.g. Ctrl+S, Ctrl+N)
        if modifiers & Qt.ControlModifier:
            combo = (key, Qt.ControlModifier)
            if combo in self.global_keymap:
                action_id = self.global_keymap[combo]
                logging.debug(f"[INPUT_SYSTEM] Ctrl+key combo mapped to action {action_id}")
                registry.execute(action_id, self.api.context)
                return True

        # 2. Simple Keymap Lookup (Single keys like 'R' or 'Delete')
        if key in self.global_keymap:
            action_id = self.global_keymap[key]
            logging.debug(f"[INPUT_SYSTEM] Key {key} mapped to action {action_id}")
            # Avoid triggering undo/redo without Ctrl
            if action_id in ["edit.undo", "edit.redo"] and not (modifiers & Qt.ControlModifier):
                logging.debug("[INPUT_SYSTEM] Ignoring z/y without ctrl")
                return False
            logging.debug(f"[INPUT_SYSTEM] Executing action {action_id} via registry")
            registry.execute(action_id, self.api.context)
            return True

        logging.debug(f"[INPUT_SYSTEM] No action mapped for key {key}")
        return False

    def _load_keymap(self):
        """Parse the YAML config for keymap definitions, supporting 'global' and 'commands' sections."""
        if not self.config_path or not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                # Support legacy 'commands' section
                commands = data.get('commands', [])
                for cmd in commands:
                    key_char = cmd.get('default_key')
                    action_id = cmd.get('id')
                    if key_char and action_id:
                        key_name = f"Key_{key_char.upper()}"
                        if hasattr(Qt, key_name):
                            qt_key = getattr(Qt, key_name)
                            self.global_keymap[qt_key] = action_id
                # Support new 'global' section
                global_map = data.get('global', {})
                for key_str, action_id in global_map.items():
                    # Handle modifier keys (e.g., Ctrl+Z)
                    if key_str.startswith("Ctrl+"):
                        base_key = key_str.split("+")[1]
                        key_name = f"Key_{base_key.upper()}"
                        if hasattr(Qt, key_name):
                            qt_key = getattr(Qt, key_name)
                            # Store tuple (key, modifier) for lookup
                            self.global_keymap[(qt_key, Qt.ControlModifier)] = action_id
                    else:
                        key_name = f"Key_{key_str.upper()}"
                        if hasattr(Qt, key_name):
                            qt_key = getattr(Qt, key_name)
                            self.global_keymap[qt_key] = action_id
        except Exception as e:
            logging.warning(f"[INPUT_SYSTEM] Failed to load keymap from {self.config_path}: {e}")