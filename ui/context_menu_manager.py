"""
Context menu manager for Talus Trace UI.

Manages context menu creation and execution based on selection state and config.
"""

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction, QCursor
from api.manager import APIManager
from api.actions import registry
from infra.logging import infra_log

class ContextMenuManager:
    """Manages context menu creation and execution based on selection state and config."""
    def __init__(self, config=None, actions_map=None):
        """Initialize ContextMenuManager with optional config and actions map."""
        self.config = config or {}
        # Map of "action_id" -> {"label": "Display Name", "action": "command.id"}
        self.actions_map = actions_map or {}

    def build_menu(self, menu_type=None, parent=None):
        from infra.logging import infra_log
        infra_log(f"[DEBUG][ContextMenuManager] build_menu START: menu_type={menu_type}", level="debug")
        from infra.logging import infra_log
        infra_log(f"[DIAG][ContextMenuManager] build_menu called with menu_type={menu_type}", level="info")
        infra_log(f"[DIAG][ContextMenuManager] config: {self.config}", level="info")
        infra_log(f"[DIAG][ContextMenuManager] actions_map: {self.actions_map}", level="info")
        """
        Build and return a QMenu for the given menu_type using config or actions_map.
        If menu_type is None, falls back to actions_map for generic menu.
        """
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        from ui.i18n import I18N
        menu = QMenu(parent)
        actions_added = []
        # Use YAML config for context menus if available
        context_menus = self.config.get('context_menu', {}) if self.config else {}
        if menu_type and menu_type in context_menus:
            for entry in context_menus[menu_type]:
                if entry.get('separator', False):
                    menu.addSeparator()
                    actions_added.append('separator')
                elif 'uuid' in entry:
                    uuid = entry['uuid']
                    label = I18N.get(uuid)
                    infra_log(f"[DEBUG][ContextMenuManager] Adding action: label={label}, uuid={uuid}", level="debug")
                    if not label or not isinstance(label, str):
                        raise AssertionError(f"Missing i18n label for UUID: {uuid}")
                    action = QAction(label, menu)
                    action.setData(uuid)
                    infra_log(f"[DEBUG][ContextMenuManager] QAction created: text={action.text()}, data={action.data()}", level="debug")
                    action.triggered.connect(lambda checked=False, cid=uuid: self._execute(cid))
                    menu.addAction(action)
                    actions_added.append(f"{label} ({uuid})")
                elif 'command' in entry:
                    cmd_id = entry['command']
                    uuid = None
                    if self.actions_map and cmd_id in self.actions_map:
                        uuid = self.actions_map[cmd_id].get('uuid')
                    if not uuid:
                        raise AssertionError(f"Context menu entry for command '{cmd_id}' is missing a UUID mapping in actions_map. All context menu actions must have a UUID.")
                    label = I18N.get(uuid)
                    infra_log(f"[DEBUG][ContextMenuManager] Adding action (from command): label={label}, uuid={uuid}, cmd_id={cmd_id}", level="debug")
                    if not label or not isinstance(label, str):
                        raise AssertionError(f"Missing i18n label for UUID: {uuid} (from command: {cmd_id})")
                    action = QAction(label, menu)
                    action.setData(uuid)
                    infra_log(f"[DEBUG][ContextMenuManager] QAction created: text={action.text()}, data={action.data()}", level="debug")
                    action.triggered.connect(lambda checked=False, cid=uuid: self._execute(cid))
                    menu.addAction(action)
                    actions_added.append(f"{label} ({uuid})")
        elif self.actions_map:
            for key, details in self.actions_map.items():
                uuid = details.get("uuid", key)
                label = I18N.get(uuid)
                infra_log(f"[DEBUG][ContextMenuManager] Adding action (actions_map): label={label}, uuid={uuid}, key={key}", level="debug")
                if not label or not isinstance(label, str):
                    raise AssertionError(f"Missing i18n label for UUID: {uuid}")
                action = QAction(label, menu)
                action.setData(uuid)
                infra_log(f"[DEBUG][ContextMenuManager] QAction created: text={action.text()}, data={action.data()}", level="debug")
                action.triggered.connect(lambda checked=False, cid=uuid: self._execute(cid))
                menu.addAction(action)
                actions_added.append(f"{label} ({uuid})")
        else:
            action = QAction(I18N.get("no_actions_configured", "No Actions Configured"), menu)
            action.setEnabled(False)
            menu.addAction(action)
            actions_added.append("No Actions Configured")
        infra_log(f"[DIAG][ContextMenuManager] build_menu actions_added: {actions_added}", level="info")
        infra_log(f"[DEBUG][ContextMenuManager] build_menu END: menu_type={menu_type}, actions={[{'text': a.text(), 'data': a.data()} for a in menu.actions()]}", level="debug")
        return menu

    def show_context_menu(self, event, item=None, menu_type=None):
        """Build and display the context menu at the mouse position. Uses item to select menu type."""
        infra_log(f"[DIAG][ContextMenuManager] show_context_menu called: event={event}, item={item}, menu_type={menu_type}, item_type={type(item)}", level="info")
        # Determine menu type based on item
        if menu_type is not None:
            mtype = menu_type
        else:
            # Determine menu type based on item type
            mtype = 'canvas'
            if item is not None:
                try:
                    from ui.items.device import DeviceItem
                except Exception:
                    DeviceItem = None
                try:
                    from ui.items.wire import WireItem
                except Exception:
                    WireItem = None
                try:
                    from ui.items.pin import PinItem
                except Exception:
                    PinItem = None
                if DeviceItem and isinstance(item, DeviceItem):
                    mtype = 'device'
                elif WireItem and isinstance(item, WireItem):
                    mtype = 'wire'
                elif PinItem and isinstance(item, PinItem):
                    mtype = 'pin'
                else:
                    mtype = 'canvas'
        infra_log(f"[DIAG][ContextMenuManager] show_context_menu: resolved mtype={mtype}", level="info")
        menu = self.build_menu(menu_type=mtype)
        infra_log(f"[DIAG][ContextMenuManager] show_context_menu: menu actions={[a.text() for a in menu.actions()]}", level="info")
        # Dispatch 'context_menu' event for test hooks and observers
        try:
            from api.manager import APIManager
            api = APIManager.get_instance()
            api.dispatch('context_menu', {'menu': menu, 'event': event, 'item': item, 'menu_type': mtype})
            infra_log(f"Dispatched context_menu event: menu_type={mtype}, item={item}", level="info")
        except Exception as e:
            infra_log(f"Exception dispatching context_menu: {e}", level="error")
        if hasattr(event, 'globalPos'):
            menu.exec(event.globalPos())
        elif hasattr(event, 'screenPos'):
            menu.exec(event.screenPos())
        else:
            menu.exec(QCursor.pos())

    def _execute(self, action_uuid):
        """Helper to run the command via the API registry. Attaches selected model to context for dispatcher actions."""
        try:
            # Accept both UUID and legacy string for backward compatibility
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
                if hasattr(model, "device_id") and hasattr(model, "id"):
                    api.context.pin = model
                    if hasattr(model, "device_id"):
                        device = next((d for d in api.context.harness.devices if getattr(d, "id", None) == getattr(model, "device_id", None)), None)
                        if device:
                            api.context.device = device
                elif hasattr(model, "pins"):
                    api.context.device = model
                elif hasattr(model, "segments"):
                    api.context.wire = model
            # For delete, set logging flag for testability (legacy support)
            if action_uuid in ("edit.delete", "e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b"):
                if hasattr(api.context, '__dict__'):
                    before = getattr(api.context, '_test_logging_flag', None)
                    infra_log(f"[DEBUG] Before setting _test_logging_flag: {before}", level="info")
                    api.context.__dict__["_test_logging_flag"] = True
                    after = getattr(api.context, '_test_logging_flag', None)
                    infra_log(f"[DEBUG] After setting _test_logging_flag: {after}", level="info")
            # Try UUID first, then fallback to string
            if action_uuid in registry:
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