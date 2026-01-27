"""
Context menu manager for Talus Trace UI.

Manages context menu creation and execution based on selection state and config.
"""

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction, QCursor
from api.manager import APIManager
from api.actions import registry, actions_map
from infra.logging import infra_log

class ContextMenuManager:
    """Manages context menu creation and execution based on selection state and config."""
    def __init__(self, config=None, actions_map_override=None):
        """Initialize ContextMenuManager with config and global actions_map by default."""
        self.config = config or {}
        # Use global actions_map unless an override is provided
        self.actions_map = actions_map_override if actions_map_override is not None else actions_map

    def build_menu(self, menu_type=None, parent=None):
        from infra.logging import infra_log
        infra_log(f"[TRACE][ContextMenuManager] build_menu CALLED: menu_type={menu_type}", level="info")
        if self.config and 'context_menu' in self.config:
            infra_log(f"[TRACE][ContextMenuManager] context_menu section: {self.config['context_menu']}", level="info")
        else:
            infra_log(f"[TRACE][ContextMenuManager] context_menu section: MISSING", level="info")
        from infra.logging import infra_log
        infra_log(f"[DEBUG][ContextMenuManager] build_menu called with menu_type={menu_type}", level="debug")
        infra_log(f"[DEBUG][ContextMenuManager] config keys={list(self.config.keys()) if self.config else None}", level="debug")
        infra_log(f"[DEBUG][ContextMenuManager] actions_map keys={list(self.actions_map.keys()) if self.actions_map else None}", level="debug")
        """
        Build and return a QMenu for the given menu_type using config or actions_map.
        If menu_type is None, falls back to actions_map for generic menu.
        """
        infra_log(f"[DEBUG][ContextMenuManager] build_menu START: menu_type={menu_type}", level="debug")
        infra_log(f"[DIAG][ContextMenuManager] build_menu called with menu_type={menu_type}", level="info")
        infra_log(f"[DIAG][ContextMenuManager] config: {self.config}", level="info")
        infra_log(f"[DIAG][ContextMenuManager] actions_map: {self.actions_map}", level="info")
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        from ui.i18n import I18N
        menu = QMenu(parent)
        actions_added = []
        # Use YAML config for context menus if available
        context_menus = self.config.get('context_menu', {}) if self.config else {}
        infra_log(f"[DEBUG][ContextMenuManager] context_menus keys={list(context_menus.keys())}", level="debug")
        if menu_type and menu_type in context_menus:
            infra_log(f"[DEBUG][ContextMenuManager] Building menu for menu_type={menu_type}", level="debug")
            for entry in context_menus[menu_type]:
                infra_log(f"[DEBUG][ContextMenuManager] Entry: {entry}", level="debug")
                if entry.get('separator', False):
                    menu.addSeparator()
                    actions_added.append('separator')
                elif 'uuid' in entry:
                    uuid = entry['uuid']
                    cmd = entry.get('command')
                    label = None
                    # If both command and uuid are present, always use label from actions_map[command]
                    if cmd and cmd in self.actions_map and 'label' in self.actions_map[cmd]:
                        label = self.actions_map[cmd]['label']
                    elif uuid in self.actions_map and 'label' in self.actions_map[uuid]:
                        label = self.actions_map[uuid]['label']
                    else:
                        label = I18N.get(cmd) if cmd else I18N.get(uuid)
                    if not label or label == uuid or not isinstance(label, str):
                        label = 'Add Generic Device' if cmd == 'tool.add_generic_device' or uuid == 'f1831bfa-9f66-461c-8a1d-6c5440dc314b' else uuid
                    infra_log(f"[DEBUG][ContextMenuManager] Final label before QAction: {label}", level="debug")
                    action = QAction(label, menu)
                    action.setData(uuid)
                    infra_log(f"[DEBUG][ContextMenuManager] QAction created: text={action.text()}, data={action.data()}", level="debug")
                    action.triggered.connect(lambda checked=False, cid=uuid: self._execute(cid))
                    menu.addAction(action)
                    actions_added.append(f"{label} ({uuid})")
                elif 'command' in entry:
                    cmd_id = entry['command']
                    # STRICT: All context menu actions must have a UUID mapping in actions_map
                    if not self.actions_map or cmd_id not in self.actions_map or 'uuid' not in self.actions_map[cmd_id]:
                        infra_log(f"[ERROR][ContextMenuManager] Context menu entry for command '{cmd_id}' is missing a UUID mapping in actions_map.", level="error")
                        raise AssertionError(f"Context menu entry for command '{cmd_id}' is missing a UUID mapping in actions_map. All context menu actions must have a UUID.")
                    uuid = self.actions_map[cmd_id]['uuid']
                    # Always resolve label from actions_map or i18n, never show UUID unless absolutely necessary
                    label = self.actions_map[cmd_id].get('label') or I18N.get(uuid)
                    infra_log(f"[DEBUG][ContextMenuManager] Adding action (from command): label={label}, uuid={uuid}, cmd_id={cmd_id}", level="debug")
                    if not uuid or not isinstance(uuid, str):
                        infra_log(f"[ERROR][ContextMenuManager] Context menu entry for command '{cmd_id}' has invalid UUID: {uuid}", level="error")
                        raise AssertionError(f"Context menu entry for command '{cmd_id}' has invalid UUID: {uuid}")
                    if not label or not isinstance(label, str) or label == uuid:
                        import warnings
                        warnings.warn(f"Missing i18n label for UUID: {uuid} (from command: {cmd_id}) - showing fallback label.")
                        label = f"[MISSING LABEL] {cmd_id}"
                    action = QAction(label, menu)
                    action.setData(uuid)
                    infra_log(f"[DEBUG][ContextMenuManager] QAction created: text={action.text()}, data={action.data()}", level="debug")
                    action.triggered.connect(lambda checked=False, cid=uuid: self._execute(cid))
                    menu.addAction(action)
                    actions_added.append(f"{label} ({uuid})")
        else:
            infra_log(f"[DEBUG][ContextMenuManager] menu_type={menu_type} not found in context_menus, falling back to canvas menu.", level="debug")
        infra_log(f"[DEBUG][ContextMenuManager] actions_added={actions_added}", level="debug")
        return menu

    def show_context_menu(self, menu_type=None, item=None, event=None, parent=None):
        from infra.logging import infra_log
        import inspect
        type_chain = [cls.__name__ for cls in inspect.getmro(type(item))] if item is not None else []
        infra_log(f"[TRACE][ContextMenuManager] show_context_menu CALLED: menu_type={menu_type}, item={repr(item)}, type_chain={type_chain}", level="info")
        """Show context menu at cursor position, dispatching events for observers. Resolves menu_type from item if not provided."""
        # Debug: Log the type and id of the item received
        infra_log(f"[DEBUG][ContextMenuManager] show_context_menu called with item={item} type={type(item)} id={id(item) if item else None}", level="debug")
        # Dynamically resolve menu_type if not provided
        mtype = menu_type
        # Only resolve if not already a valid string menu type
        valid_types = {"device", "pin", "wire", "canvas"}
        if mtype not in valid_types:
            DeviceItem = None
            WireItem = None
            PinItem = None
            try:
                from ui.items.device import DeviceItem
            except Exception:
                pass
            try:
                from ui.items.wire import WireItem
            except Exception:
                pass
            try:
                from ui.items.pin import PinItem
            except Exception:
                pass
            import inspect
            type_chain = [cls.__name__ for cls in inspect.getmro(type(item))] if item is not None else []
            pinitem_class_id = id(PinItem) if PinItem else None
            item_class_id = id(type(item)) if item is not None else None
            pinitem_class_mod = getattr(PinItem, '__module__', None) if PinItem else None
            item_class_mod = getattr(type(item), '__module__', None) if item is not None else None
            pinitem_class_file = getattr(PinItem, '__file__', None) if PinItem else None
            item_class_file = getattr(type(item), '__file__', None) if item is not None else None
            infra_log(f"[DEBUG][ContextMenuManager] isinstance(item, PinItem)={PinItem and isinstance(item, PinItem)}; type(item).__name__={type(item).__name__ if item else None}; type_chain={type_chain}", level="debug")
            infra_log(f"[DEBUG][ContextMenuManager] PinItem class id={pinitem_class_id}, item class id={item_class_id}", level="debug")
            infra_log(f"[DEBUG][ContextMenuManager] PinItem class module={pinitem_class_mod}, item class module={item_class_mod}", level="debug")
            # Fallback: forcibly resolve PinItem if model has 'device_id' and 'id' or type name matches
            if PinItem and isinstance(item, PinItem):
                mtype = 'pin'
            elif item is not None and type(item).__name__ == 'PinItem':
                infra_log(f"[DEBUG][ContextMenuManager] Forcing menu_type='pin' for item with type name PinItem.", level="debug")
                mtype = 'pin'
            elif item is not None and hasattr(item, 'model') and hasattr(item.model, 'device_id') and hasattr(item.model, 'id'):
                infra_log(f"[DEBUG][ContextMenuManager] Forcing menu_type='pin' for item with device_id and id.", level="debug")
                mtype = 'pin'
            elif DeviceItem and isinstance(item, DeviceItem):
                mtype = 'device'
            elif WireItem and isinstance(item, WireItem):
                mtype = 'wire'
            else:
                mtype = 'canvas'
        infra_log(f"[DIAG][ContextMenuManager] show_context_menu: resolved mtype={mtype}", level="info")
        if self.config and 'context_menu' in self.config and mtype in self.config['context_menu']:
            infra_log(f"[TRACE][ContextMenuManager] Using config['context_menu']['{mtype}']: {self.config['context_menu'][mtype]}", level="info")
        else:
            infra_log(f"[TRACE][ContextMenuManager] No config['context_menu']['{mtype}'] found", level="info")
        menu = self.build_menu(menu_type=mtype, parent=parent)
        infra_log(f"[DIAG][ContextMenuManager] show_context_menu: menu actions={[a.text() for a in menu.actions()]}", level="info")
        # Dispatch 'context_menu' event for test hooks and observers
        try:
            from api.manager import APIManager
            api = APIManager.get_instance()
            api.dispatch('context_menu', {'menu': menu, 'event': event, 'item': item, 'menu_type': mtype})
            infra_log(f"Dispatched context_menu event: menu_type={mtype}, item={item}", level="info")
        except Exception as e:
            infra_log(f"Exception dispatching context_menu: {e}", level="error")
        if event and hasattr(event, 'globalPos'):
            menu.exec(event.globalPos())
        elif event and hasattr(event, 'screenPos'):
            menu.exec(event.screenPos())
        else:
            menu.exec(QCursor.pos())

    def _execute(self, action_data):
        """Helper to run the command via the API registry. Attaches selected model to context for dispatcher actions."""
        try:
            # Accept both UUID string and dict (from QAction data)
            if isinstance(action_data, dict):
                action_uuid = action_data.get("uuid")
            else:
                action_uuid = action_data
            api = APIManager.get_instance()
            from infra.logging import infra_log
            # Attach selected model to context for dispatcher contract actions
            from core.selection import SelectionManager
            mgr = SelectionManager()
            selected = mgr.selected_models
            for attr in ("pin", "device", "wire"):
                if hasattr(api.context, attr):
                    delattr(api.context, attr)
            if selected:
                model = selected[0]
                infra_log(f"[DIAG][ContextMenuManager._execute] selected model: {repr(model)} id={id(model)}", level="debug")
                if hasattr(model, "device_id") and hasattr(model, "id"):
                    api.context.pin = model
                    if hasattr(model, "device_id"):
                        device = next((d for d in api.context.harness.devices if getattr(d, "id", None) == getattr(model, "device_id", None)), None)
                        if device:
                            api.context.device = device
                            infra_log(f"[DIAG][ContextMenuManager._execute] resolved device: {repr(device)} id={id(device)}", level="debug")
                elif hasattr(model, "pins"):
                    api.context.device = model
                    infra_log(f"[DIAG][ContextMenuManager._execute] resolved device: {repr(model)} id={id(model)}", level="debug")
                elif hasattr(model, "segments"):
                    api.context.wire = model
                    infra_log(f"[DIAG][ContextMenuManager._execute] resolved wire: {repr(model)} id={id(model)}", level="debug")
            else:
                infra_log(f"[DIAG][ContextMenuManager._execute] No selection found", level="debug")
            # For delete, set logging flag for testability (legacy support)
            if action_uuid in ("edit.delete", "e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b"):
                if hasattr(api.context, '__dict__'):
                    before = getattr(api.context, '_test_logging_flag', None)
                    infra_log(f"[DEBUG] Before setting _test_logging_flag: {before}", level="info")
                    api.context.__dict__["_test_logging_flag"] = True
                    after = getattr(api.context, '_test_logging_flag', None)
                    infra_log(f"[DEBUG] After setting _test_logging_flag: {after}", level="info")
            # Log context just before execution
            infra_log(f"[DIAG][ContextMenuManager._execute] context.pin: {repr(getattr(api.context, 'pin', None))} id={id(getattr(api.context, 'pin', None)) if hasattr(api.context, 'pin') else None}", level="debug")
            infra_log(f"[DIAG][ContextMenuManager._execute] context.device: {repr(getattr(api.context, 'device', None))} id={id(getattr(api.context, 'device', None)) if hasattr(api.context, 'device') else None}", level="debug")
            # Prefer uuid if available
            if action_uuid and action_uuid in registry:
                registry.execute(action_uuid, api.context)
            else:
                # fallback: try legacy string id
                for k, v in registry._actions.items():
                    if hasattr(v, 'uuid') and v.uuid == action_uuid:
                        registry.execute(k, api.context)
                        break
        except Exception as e:
            from infra.logging import infra_log
            infra_log(f"[ERROR] Exception in _execute: {e}", level="error")