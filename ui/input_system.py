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
        self.global_keymap = {}  # {Qt.Key: action_id}
        self._move_tool = move_tool  # Allow dependency injection for tests
        # Register edit.delete action (avoids circular import)
        import api.edit_delete_action
        # 1. Load Defaults (Safety Net)
        self._load_defaults()
        # 2. Override with Config if available
        if self.config_path:
            self._load_keymap()

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
        self.global_keymap[Qt.Key_Z] = "edit.undo"
        self.global_keymap[Qt.Key_Y] = "edit.redo"
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
        import sys
        print(f"[DEBUG][handle_canvas_event] EVENT TYPE: {etype} ({event.original_event.__class__.__name__})", file=sys.stderr)
        tool = self._move_tool if self._move_tool is not None else self.api.tool_manager.active_tool
        # Use API facade instead of direct Core access
        selection_ids = self.api.get_selection()
        is_move_tool = tool.__class__.__name__ == "MoveTool"
        scene_pos = getattr(event, 'scene_pos', None)
        item = getattr(event, 'scene_item', None) or getattr(event, 'item_at', None)
        print(f"[DEBUG][handle_canvas_event] BEFORE itemAt: item={item}, scene_pos={scene_pos}", file=sys.stderr)
        print(f"[DEBUG][handle_canvas_event] has main_window={hasattr(self.api, 'main_window')}, has canvas={hasattr(self.api.main_window, 'canvas') if hasattr(self.api, 'main_window') else False}", file=sys.stderr)
        # If item is still None and we have a main_window with canvas, query the scene directly
        if item is None and scene_pos is not None:
            try:
                if hasattr(self.api, 'main_window') and hasattr(self.api.main_window, 'canvas'):
                    canvas = self.api.main_window.canvas
                    print(f"[DEBUG][handle_canvas_event] canvas={canvas}, has scene attr={hasattr(canvas, 'scene')}", file=sys.stderr)
                    if canvas and hasattr(canvas, 'scene'):
                        from PySide6.QtGui import QTransform
                        scene = canvas.scene
                        print(f"[DEBUG][handle_canvas_event] scene={scene}, about to call itemAt", file=sys.stderr)
                        if scene:
                            item = scene.itemAt(scene_pos, QTransform())
                            print(f"[DEBUG][handle_canvas_event] AFTER itemAt: item={item}, type={type(item)}, hasattr model={hasattr(item, 'model') if item else None}", file=sys.stderr)
                    else:
                        print(f"[DEBUG][handle_canvas_event] scene check failed", file=sys.stderr)
            except Exception as e:
                logging.warning(f"[InputSystem.handle_canvas_event] Failed to get item at scene position: {e}")
                import traceback
                traceback.print_exc()
                item = None
        logging.debug(f"[InputSystem.handle_canvas_event] CALLED: etype={etype}, tool={tool}, selection_ids={selection_ids}, scene_pos={scene_pos}, item={item}, event={event}, orig_event={event.original_event}")
        # 1. Right Click Handling (Context Menu)
        if etype == QEvent.MouseButtonPress:
            btn_val = event.button() if hasattr(event, 'button') and callable(event.button) else getattr(event, 'button', None)
            orig_btn_val = event.original_event.button() if hasattr(event.original_event, 'button') and callable(event.original_event.button) else getattr(event.original_event, 'button', None)
            logging.debug(f"[INPUT_SYSTEM][MOUSE_PRESS] event.button={btn_val} (type={type(btn_val)}), orig_event.button={orig_btn_val} (type={type(orig_btn_val)}) Qt.RightButton={Qt.RightButton}")
            is_right_click = btn_val == Qt.RightButton or orig_btn_val == Qt.RightButton
            if is_right_click:
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
                if tool and hasattr(tool, 'on_mouse_press'):
                    tool.on_mouse_press(event)
                return True
        # 2. Tool Handling
        if tool:
            if etype == QEvent.MouseButtonPress:
                logging.debug(f"[INPUT_SYSTEM][MOUSE_PRESS] tool={tool}, item={item}")
                if hasattr(tool, 'start_drag'):
                    if is_move_tool:
                        if selection_ids and item is not None and hasattr(item, 'model') and getattr(item.model, 'id', None) in selection_ids:
                            tool.start_drag(item, scene_pos)
                        elif item is not None and hasattr(item, 'model') and getattr(item.model, 'id', None) not in selection_ids:
                            self.api.select([item.model.id], tool_name="move")
                    else:
                        tool.start_drag(item, scene_pos)
                if hasattr(tool, 'on_mouse_press'):
                    logging.debug(f"[InputSystem.handle_canvas_event] Calling tool.on_mouse_press for tool={tool}")
                    tool.on_mouse_press(event)
            elif etype == QEvent.MouseMove:
                logging.debug(f"[INPUT_SYSTEM][MOUSE_MOVE] tool={tool}, scene_pos={scene_pos}")
                if hasattr(tool, 'update_drag'):
                    if is_move_tool:
                        if selection_ids:
                            tool.update_drag(scene_pos)
                    else:
                        tool.update_drag(scene_pos)
                if hasattr(tool, 'on_mouse_move'):
                    tool.on_mouse_move(event)
            elif etype == QEvent.MouseButtonRelease:
                logging.debug(f"[INPUT_SYSTEM][MOUSE_RELEASE] tool={tool}, scene_pos={scene_pos}")
                if hasattr(tool, 'finish_drag'):
                    if is_move_tool:
                        if selection_ids:
                            tool.finish_drag(scene_pos)
                    else:
                        tool.finish_drag(scene_pos)
                if hasattr(tool, 'on_mouse_release'):
                    tool.on_mouse_release(event)
        return False

    def eventFilter(self, obj, event):
        """
        InputSystem event filter for mouse/keyboard events.
        Always install this on the QGraphicsView's viewport for robust mouse event handling.
        This method will resolve the parent QGraphicsView for coordinate mapping.
        """
        logging.debug(f"[InputSystem.eventFilter] CALLED: obj={obj}, event={event}, type={event.type()} ({event.__class__.__name__})")
        if event.type() == QEvent.KeyPress:
            if self._handle_key(event):
                return True
        # Route mouse and context menu events to handle_canvas_event
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseMove, QEvent.ContextMenu):
            logging.debug(f"[InputSystem.eventFilter] Routing mouse event type={event.type()} to handle_canvas_event: event={event}")
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

        # 1. Check Global Keymap
        # Handle Modifier Logic (Simple implementation for Ctrl+Z)
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Z:
                logging.debug("[INPUT_SYSTEM] Ctrl+Z detected, executing edit.undo")
                registry.execute("edit.undo", self.api.context)
                return True
            if key == Qt.Key_Y:
                logging.debug("[INPUT_SYSTEM] Ctrl+Y detected, executing edit.redo")
                registry.execute("edit.redo", self.api.context)
                return True

        # 2. Simple Keymap Lookup (Single keys like 'R' or 'Delete')
        if key in self.global_keymap:
            action_id = self.global_keymap[key]
            logging.debug(f"[INPUT_SYSTEM] Key {key} mapped to action {action_id}")
            # Avoid re-triggering undo/redo if caught above
            if action_id in ["edit.undo", "edit.redo"] and not (modifiers & Qt.ControlModifier):
                logging.debug("[INPUT_SYSTEM] Ignoring z/y without ctrl")
                pass # Ignore 'z' without ctrl
            else:
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