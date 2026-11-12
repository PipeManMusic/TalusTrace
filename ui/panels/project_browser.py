
"""
Project Browser panel for Talus Trace UI.

Displays devices, wires and bundles in a tree structure and synchronizes with
selection/model changes. Provides per-item visibility toggling (checkboxes) and
user-defined visibility groups whose members can be shown/hidden together.
All model mutation is routed through the APIManager (never mutated directly).
"""
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QMenu,
    QInputDialog,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from api.manager import APIManager
from ui.i18n import I18N

# Item data roles.
ROLE_ID = 100        # Model/group id (kept as 100 for backward compatibility).
ROLE_KIND = 101      # One of: device, wire, bundle, category, group, member.
ROLE_GROUP_ID = 102  # Owning group id for member/group nodes.

# Category kinds that map to a harness collection.
_CATEGORY_KINDS = ("device", "wire", "bundle")


class ProjectBrowser(QWidget):
    """
    ProjectBrowser panel widget displaying devices, wires and bundles in a tree.

    Supports show/hide of individual items and of user-defined groups via
    checkboxes, synchronizing with selection and model changes from APIManager.
    """
    def list_devices(self):
        """
        Return a list of device IDs currently shown in the Devices group.
        Returns:
            list: List of device IDs.
        """
        ids = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            if group.data(0, ROLE_KIND) == "category" and group.data(0, ROLE_ID) == "device":
                for j in range(group.childCount()):
                    dev_id = group.child(j).data(0, ROLE_ID)
                    if dev_id:
                        ids.append(dev_id)
        return ids

    @property
    def devices(self):
        """
        Return the list of device models currently in the harness (mirrors what is shown in the browser).
        """
        if hasattr(self.api, 'context') and self.api.context and hasattr(self.api.context, 'harness'):
            return list(getattr(self.api.context.harness, 'devices', []))
        return []
    def __init__(self, parent=None):
        """
        Initialize the ProjectBrowser panel and set up the item tree.
        Subscribes to selection, model, visibility and group change events.
        """
        super().__init__(parent)
        self.api = APIManager.get_instance()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(I18N.get('project_browser_panel_header'))
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.tree)
        # Subscriptions
        if hasattr(self.api, 'subscribe'):
            self.api.subscribe("selection_changed", self.on_selection_changed)
            self.api.subscribe("model_changed", self._on_model_changed_event)
            # Subscribe to all *_removed events for live updates
            self.api.subscribe("device_removed", self._schedule_refresh)
            self.api.subscribe("wire_removed", self._schedule_refresh)
            self.api.subscribe("bundle_removed", self._schedule_refresh)
            self.api.subscribe("bundle_added", self._schedule_refresh)
            self.api.subscribe("pin_removed", self._schedule_refresh)
            self.api.subscribe("visibility_changed", self._schedule_refresh)
            self.api.subscribe("visibility_groups_changed", self._schedule_refresh)
        self._syncing_selection = False
        self._updating_tree = False
        self._refresh_pending = False
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.refresh()

    # ── Deferred refresh ─────────────────────────────────────────────
    def _on_model_changed_event(self, data=None):
        """Filter model_changed events and schedule a rebuild for structural ones."""
        # Structural actions change the tree contents, while 'update' actions
        # (e.g. renaming a device or pin) change derived labels such as a wire's
        # "source > dest" name. Both require a rebuild. Visibility toggles arrive
        # via the dedicated 'visibility_changed' event instead.
        if data and isinstance(data, dict) and 'action' in data:
            if data.get('action') not in ('remove', 'delete', 'add', 'load', 'update'):
                return
        self._schedule_refresh(data)

    def _schedule_refresh(self, data=None):
        """Coalesce and defer a tree rebuild to the next event-loop iteration.

        Rebuilding synchronously from inside a Qt signal (e.g. the checkbox
        ``itemChanged`` handler that triggered the model mutation) would call
        ``tree.clear()`` and delete the very item whose C++ signal is still on
        the stack — a use-after-free that segfaults. Deferring lets the signal
        stack unwind first.
        """
        if self._refresh_pending:
            return
        self._refresh_pending = True
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._do_deferred_refresh)

    def _do_deferred_refresh(self):
        """Run a pending deferred refresh."""
        self._refresh_pending = False
        self.refresh()

    # ── Tree construction ────────────────────────────────────────────
    def refresh(self, data=None):
        """
        Rebuild the tree to display current devices, wires, bundles and groups.

        Note: event-driven callers go through :meth:`_schedule_refresh` so the
        rebuild never runs synchronously inside a Qt item signal. This method
        may still be called directly (initial build and tests).
        Args:
            data (optional): Unused; accepted for signal-slot compatibility.
        """
        self._updating_tree = True
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            harness = getattr(self.api.context, 'harness', None) if getattr(self.api, 'context', None) else None
            if not harness:
                return

            # Category groups: Devices / Wires / Bundles.
            self._build_category("device", I18N.get('project_browser_group_devices', 'Devices'),
                                 list(getattr(harness, 'devices', [])))
            self._build_category("wire", I18N.get('project_browser_group_wires', 'Wires'),
                                 list(getattr(harness, 'wires', [])), label_fn=self._wire_label)
            self._build_category("bundle", I18N.get('project_browser_group_bundles', 'Bundles'),
                                 list(getattr(harness, 'bundles', [])), label_fn=self._bundle_label)

            # User-defined visibility groups.
            self._build_groups(harness)
        finally:
            self.tree.blockSignals(False)
            self._updating_tree = False

    def _build_category(self, kind, title, models, label_fn=None):
        """Build a category node (Devices/Wires/Bundles) with a checkable child per model."""
        cat = QTreeWidgetItem(self.tree, [title])
        cat.setData(0, ROLE_KIND, "category")
        cat.setData(0, ROLE_ID, kind)
        cat.setFlags(cat.flags() | Qt.ItemIsUserCheckable)
        cat.setExpanded(True)
        ids_seen = set()
        for model in models:
            mid = getattr(model, 'id', None)
            if mid is None or mid in ids_seen:
                continue
            ids_seen.add(mid)
            text = label_fn(model) if label_fn else (getattr(model, 'label', None) or mid)
            item = QTreeWidgetItem(cat, [text])
            item.setData(0, ROLE_ID, mid)
            item.setData(0, ROLE_KIND, kind)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked if getattr(model, 'visible', True) else Qt.Unchecked)
        self._apply_tristate(cat, models)

    def _build_groups(self, harness):
        """Build the Groups section with a checkable node per user-defined group."""
        groups = self.api.get_visibility_groups()
        root = QTreeWidgetItem(self.tree, [I18N.get('project_browser_groups_header', 'Groups')])
        root.setData(0, ROLE_KIND, "groups_root")
        root.setExpanded(True)
        # Lookup id -> (model, kind) for member display.
        model_map = {}
        for coll, kind in (("devices", "device"), ("wires", "wire"), ("bundles", "bundle")):
            for m in getattr(harness, coll, []):
                model_map[getattr(m, 'id', None)] = (m, kind)
        for g in groups:
            gnode = QTreeWidgetItem(root, [g.get("name", "")])
            gnode.setData(0, ROLE_KIND, "group")
            gnode.setData(0, ROLE_GROUP_ID, g.get("id"))
            gnode.setFlags(gnode.flags() | Qt.ItemIsUserCheckable)
            gnode.setExpanded(True)
            member_models = []
            for mid in g.get("members", []):
                entry = model_map.get(mid)
                if not entry:
                    continue
                model, kind = entry
                mnode = QTreeWidgetItem(gnode, [self._model_label(model, kind)])
                mnode.setData(0, ROLE_ID, mid)
                mnode.setData(0, ROLE_KIND, "member")
                mnode.setData(0, ROLE_GROUP_ID, g.get("id"))
                mnode.setFlags(mnode.flags() | Qt.ItemIsUserCheckable)
                mnode.setCheckState(0, Qt.Checked if getattr(model, 'visible', True) else Qt.Unchecked)
                member_models.append(model)
            self._apply_tristate(gnode, member_models)

    def _apply_tristate(self, parent_item, models):
        """Set a parent node's check state from its members' visibility (tri-state)."""
        if not models:
            parent_item.setCheckState(0, Qt.Unchecked)
            return
        vis = [bool(getattr(m, 'visible', True)) for m in models]
        if all(vis):
            parent_item.setCheckState(0, Qt.Checked)
        elif not any(vis):
            parent_item.setCheckState(0, Qt.Unchecked)
        else:
            parent_item.setCheckState(0, Qt.PartiallyChecked)

    # ── Labels ───────────────────────────────────────────────────────
    def _model_label(self, model, kind):
        """Return a display label for a model given its kind."""
        if kind == "wire":
            return self._wire_label(model)
        if kind == "bundle":
            return self._bundle_label(model)
        return getattr(model, 'label', None) or getattr(model, 'id', '')

    def _wire_label(self, wire):
        """Return a human-readable label for a wire."""
        harness = self.api.context.harness
        dev_map = {}
        pin_map = {}
        for dev in getattr(harness, 'devices', []):
            dev_map[dev.id] = getattr(dev, 'label', None) or dev.id
            for pin in getattr(dev, 'pins', []):
                pin_map[pin.id] = getattr(pin, 'label', None) or pin.id
        f_dev = dev_map.get(getattr(wire, 'from_conn', ''), '?')
        f_pin = pin_map.get(getattr(wire, 'from_pin', ''), '?')
        t_dev = dev_map.get(getattr(wire, 'to_conn', ''), '?')
        t_pin = pin_map.get(getattr(wire, 'to_pin', ''), '?')
        return f"{f_dev}>{f_pin} \u2192 {t_dev}>{t_pin}"

    def _bundle_label(self, bundle):
        """Return a human-readable label for a bundle."""
        meta = getattr(bundle, 'meta', None) or {}
        if meta.get('name'):
            return meta['name']
        count = len(getattr(bundle, 'wire_ids', []) or [])
        return f"Bundle ({count})"

    # ── Checkbox handling ────────────────────────────────────────────
    def _leaf_ids(self, parent_item):
        """Return the model IDs of a parent node's direct children."""
        ids = []
        for i in range(parent_item.childCount()):
            cid = parent_item.child(i).data(0, ROLE_ID)
            if cid:
                ids.append(cid)
        return ids

    def _on_item_changed(self, item, column):
        """Route a checkbox toggle to the appropriate visibility API call."""
        if self._updating_tree:
            return
        kind = item.data(0, ROLE_KIND)
        visible = item.checkState(0) == Qt.Checked
        if kind in _CATEGORY_KINDS or kind == "member":
            item_id = item.data(0, ROLE_ID)
            if item_id:
                self.api.set_item_visibility([item_id], visible)
        elif kind == "category":
            child_ids = self._leaf_ids(item)
            if child_ids:
                self.api.set_item_visibility(child_ids, visible)
        elif kind == "group":
            group_id = item.data(0, ROLE_GROUP_ID)
            if group_id:
                self.api.set_group_visibility(group_id, visible)

    # ── Context menu (group management) ──────────────────────────────
    def _selected_item_ids(self):
        """Return IDs of selected device/wire/bundle/member leaf nodes."""
        ids = []
        for it in self.tree.selectedItems():
            if it.data(0, ROLE_KIND) in _CATEGORY_KINDS or it.data(0, ROLE_KIND) == "member":
                mid = it.data(0, ROLE_ID)
                if mid and mid not in ids:
                    ids.append(mid)
        return ids

    def _on_context_menu(self, pos):
        """Build and show the context menu for group management and show/hide."""
        item = self.tree.itemAt(pos)
        menu = QMenu(self.tree)
        item_ids = self._selected_item_ids()

        if item is not None and item.data(0, ROLE_KIND) == "group":
            group_id = item.data(0, ROLE_GROUP_ID)
            menu.addAction(I18N.get('project_browser_rename_group', 'Rename Group\u2026'),
                           lambda: self._rename_group(group_id))
            menu.addAction(I18N.get('project_browser_delete_group', 'Delete Group'),
                           lambda: self.api.delete_visibility_group(group_id))
        elif item_ids:
            menu.addAction(I18N.get('project_browser_show', 'Show'),
                           lambda: self.api.set_item_visibility(item_ids, True))
            menu.addAction(I18N.get('project_browser_hide', 'Hide'),
                           lambda: self.api.set_item_visibility(item_ids, False))
            add_menu = menu.addMenu(I18N.get('project_browser_add_to_group', 'Add to Group'))
            for g in self.api.get_visibility_groups():
                gid = g.get("id")
                add_menu.addAction(g.get("name", ""),
                                   lambda checked=False, gid=gid: self.api.add_items_to_group(gid, item_ids))
            add_menu.addSeparator()
            add_menu.addAction(I18N.get('project_browser_new_group', 'New Group\u2026'),
                               lambda: self._create_group(item_ids))
            member_groups = self._groups_containing(item_ids)
            if member_groups:
                rm_menu = menu.addMenu(I18N.get('project_browser_remove_from_group', 'Remove from Group'))
                for g in member_groups:
                    gid = g.get("id")
                    rm_menu.addAction(g.get("name", ""),
                                      lambda checked=False, gid=gid: self.api.remove_items_from_group(gid, item_ids))
        else:
            menu.addAction(I18N.get('project_browser_new_group', 'New Group\u2026'),
                           lambda: self._create_group([]))

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _groups_containing(self, item_ids):
        """Return the groups that contain at least one of the given item IDs."""
        target = set(item_ids)
        return [g for g in self.api.get_visibility_groups()
                if target.intersection(set(g.get("members", [])))]

    def _create_group(self, item_ids):
        """Prompt for a group name and create it with the given members."""
        name, ok = QInputDialog.getText(
            self,
            I18N.get('project_browser_new_group', 'New Group\u2026'),
            I18N.get('project_browser_group_name_prompt', 'Group name:'),
        )
        if ok and name.strip():
            self.api.create_visibility_group(name.strip(), item_ids)

    def _rename_group(self, group_id):
        """Prompt for a new name and rename the given group."""
        current = ""
        for g in self.api.get_visibility_groups():
            if g.get("id") == group_id:
                current = g.get("name", "")
                break
        name, ok = QInputDialog.getText(
            self,
            I18N.get('project_browser_rename_group', 'Rename Group\u2026'),
            I18N.get('project_browser_group_name_prompt', 'Group name:'),
            text=current,
        )
        if ok and name.strip():
            self.api.rename_visibility_group(group_id, name.strip())

    # ── Selection sync ───────────────────────────────────────────────
    def on_selection_changed(self, data):
        """
        Handle selection change events from the APIManager.
        Highlights matching tree items without re-dispatching selection.
        Args:
            data: Event data containing 'selection' list.
        """
        if self._syncing_selection:
            return
        sel = data.get('selection', []) if isinstance(data, dict) else []
        sel_ids = {getattr(m, 'id', None) for m in sel if hasattr(m, 'id')}
        self.tree.blockSignals(True)
        self.tree.clearSelection()

        def walk(node):
            for i in range(node.childCount()):
                child = node.child(i)
                item_id = child.data(0, ROLE_ID)
                if item_id in sel_ids and child.data(0, ROLE_KIND) in _CATEGORY_KINDS:
                    child.setSelected(True)
                walk(child)

        walk(self.tree.invisibleRootItem())
        self.tree.blockSignals(False)

    def _on_tree_item_clicked(self, item, column):
        """
        Handle a tree item click — select the corresponding model on the canvas.
        """
        kind = item.data(0, ROLE_KIND)
        if kind not in _CATEGORY_KINDS and kind != "member":
            return
        item_id = item.data(0, ROLE_ID)
        if not item_id:
            return
        self._syncing_selection = True
        try:
            self.api.select([item_id], tool_name="ProjectBrowser")
        finally:
            self._syncing_selection = False