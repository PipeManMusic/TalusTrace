"""
API Manager for Talus Trace.

This module defines the APIManager class, which acts as the main interface between the UI, core models, and infrastructure layers. It provides methods for manipulating devices, pins, wires, bundles, selection, and scene items, and coordinates undo/redo, event dispatch, and tool management.

----
**APIManager Contract & Feature Summary**

* All add, edit, and delete operations for devices, pins, wires, and bundles MUST be performed via APIManager methods.
* The UI and dispatcher must NOT mutate the model directly, but instead call the appropriate APIManager method, which will:
    - Construct and execute the appropriate Command (e.g., AddDeviceCommand, DeletePinCommand)
    - Ensure undo/redo is supported via the UndoStack
    - Emit all necessary events for UI/model sync
    - Log all critical actions via infra_log
* This contract is enforced by contract tests. Any new entity lifecycle operation must be added to this API and tested for full coverage.

**Major Features & Methods:**

- Device Lifecycle: `add_device`, `delete_device`, `create_device`, `get_device_dict`
- Pin Lifecycle: `add_pin`, `delete_pin`
- Wire Lifecycle: `add_wire`, `delete_wire`, `move_segment`, `add_elbow`, `remove_elbow`, `move_elbow`
- Bundle Lifecycle: `add_bundle`, `delete_bundle`
- Selection: `select`, `deselect`, `clear_selection`
- Visibility: `set_item_visibility`, `find_item_by_id`
- Visibility Groups: `get_visibility_groups`, `create_visibility_group`, `rename_visibility_group`, `delete_visibility_group`, `set_group_members`, `add_items_to_group`, `remove_items_from_group`, `set_group_visibility`
- Scene Registry: `register_scene_item`, `unregister_scene_item`, `get_scene_item`, `find_pin_item`
- File/Project: `new_file`, `open_file`, `save_file`, `import_project`, `export_project`, `backup`, `autosave`, `restore_session`, `save_project`, `print_project`
- Undo/Redo: `undo`, `redo`, `inspect_undo_stack`, `inspect_redo_stack`, `view_history`
- UI/Tool: `move_tool`, `set_theme`, `toggle_project_browser`, `toggle_property_panel`, `toggle_library`, `toggle_audit_panel`, `reset_layout`, `open_context_menu`, `notify`, `log`
- Error Handling: `handle_error`

**Usage Examples:**

```python
# Add a device
api_manager.add_device(device)

# Delete a device
api_manager.delete_device(device)

# Add a pin
api_manager.add_pin(pin)

# Delete a pin
api_manager.delete_pin(pin)

# Add a wire
api_manager.add_wire(wire)

# Register a scene item
api_manager.register_scene_item(model_id, item)

# Select items
api_manager.select([device_id, pin_id])

# Undo last action
api_manager.undo()

# Save the project
api_manager.save_project("/path/to/file.yaml")
```

* See contract tests in tests/dispatcher/ and tests/ui/ for required behaviors and more examples.
----
"""

Context = None
from infra.settings import SystemSettings
from core.library_manager import LibraryManager



class APIManager:
    """
    APIManager handles the main API logic and command dispatch for Talus Trace.
    """

    def delete_device(self, device):
        """
        Delete a device from the model using DeleteDeviceCommand and push to the undo stack.
        Ensures device deletion is undoable, emits model_changed, and logs the action.
        This method MUST be used for all device deletion (UI/dispatcher must not mutate model directly).
        """
        from infra.logging import infra_log
        infra_log(f"delete_device: id={getattr(device, 'id', None)}", level="info")
        from api.commands.device import DeleteDeviceCommand
        if hasattr(self, 'context') and hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(DeleteDeviceCommand(device, context=self.context))
        else:
            DeleteDeviceCommand(device, context=self.context).execute()
    def delete_pin(self, pin):
        """
        Delete a pin from the model using DeletePinCommand and push to the undo stack.
        Ensures pin deletion is undoable, emits model_changed, and logs the action.
        This method MUST be used for all pin deletion (UI/dispatcher must not mutate model directly).
        """
        from infra.logging import infra_log
        infra_log(f"delete_pin: id={getattr(pin, 'id', None)}", level="info")
        from api.commands.device import DeletePinCommand
        if hasattr(self, 'context') and hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(DeletePinCommand(pin, context=self.context))
        else:
            DeletePinCommand(pin, context=self.context).execute()
    """
    APIManager is the main interface for all API operations, managing device, pin, wire, and bundle creation, deletion, and contract enforcement.

    ---
    **Lifecycle Methods (MANDATORY for all entity types):**
    - add_device(device): Add a device using AddDeviceCommand and push to the undo stack.
    - delete_device(device): Delete a device using DeleteDeviceCommand and push to the undo stack.
    - add_pin(pin): Add a pin using AddPinCommand and push to the undo stack.
    - delete_pin(pin): Delete a pin using DeletePinCommand and push to the undo stack.
    - add_wire(wire): Add a wire using AddWireCommand and push to the undo stack.
    - delete_wire(wire): Delete a wire using DeleteWireCommand and push to the undo stack.
    - add_bundle(bundle): Add a bundle using AddBundleCommand and push to the undo stack.
    - delete_bundle(bundle): Delete a bundle using DeleteBundleCommand and push to the undo stack.

    All such methods must:
        * Use the command pattern for undo/redo
        * Emit model_changed events for UI sync
        * Log actions via infra_log
        * Be called by the dispatcher/UI for all model mutation

    ---
    """

    def get_device_dict(self, device_id):
        """
        Return the device as a dictionary, including all pin geometry and metadata.
        Args:
            device_id (str): The UUID of the device to retrieve.
        Returns:
            dict: Device as dict, or None if not found.
        """
        for dev in getattr(self.context.harness, 'devices', []):
            if hasattr(dev, 'id') and dev.id == device_id:
                return dev.to_dict()
        return None

    def update_property(self, item, field, value):
        """
        Update a property on a model object using the command pattern and undo stack.
        The command's execute()/undo()/redo() already dispatch a single
        'model_changed' event, so this method must NOT dispatch again (doing so
        doubles every subscriber's work — e.g. a full audit and property-panel
        rebuild — and can freeze the UI on a single field edit).
        Args:
            item: The model object to update.
            field (str): The field name to update.
            value: The new value to set.
        """
        from api.commands.edit import UpdatePropertyCommand
        cmd = UpdatePropertyCommand(item, field, value)
        if hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(cmd)
        else:
            cmd.execute()

    def subscribe_to_all(self, callback):
        """
        Subscribe a callback to all API events (model, state, etc.).
        """
        if hasattr(self.context, 'observer'):
            self.context.observer.subscribe_to_all(callback)

    def create_device(self, label):
        """
        Create a device with a generated UUID and the given label, add it using the command pattern, and return the device.
        All UUID generation and device instantiation is handled in the API/infra layer.
        Returns the created device, or None if a duplicate UUID is detected (should not happen).
        """
        from infra.logging import infra_log
        infra_log(f"create_device: label={label}", level="info")
        from core.device import Device
        from api.commands.device import AddDeviceCommand
        import uuid
        device_id = str(uuid.uuid4())
        # Prevent duplicate device IDs (extremely unlikely)
        if any(getattr(dev, 'id', None) == device_id for dev in self.context.harness.devices):
            return None
        device = Device(id=device_id, label=label)
        if hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(AddDeviceCommand(device))
        else:
            AddDeviceCommand(device).execute()
        return device

    def create_device_from_part(self, part_id, label=None, x=0.0, y=0.0):
        """
        Create a device from a library part definition, populating pins with
        signal and label fields from the library.  Falls back to create_device()
        if the part_id is not found in the library.
        Args:
            part_id (str): The library part identifier (e.g. 'SPLICE-4W-SEALED').
            label (str, optional): Device label; defaults to part_id.
        Returns:
            Device: The created device with pre-populated pins.
        """
        from infra.logging import infra_log
        infra_log(f"create_device_from_part: part_id={part_id}", level="info")
        parts = self.library.get_parts()
        part_def = parts.get(part_id)
        if not part_def:
            return self.create_device(label or part_id)

        from core.device import Device
        from core.pin import Pin
        from api.commands.device import AddDeviceCommand
        import uuid

        device_id = str(uuid.uuid4())
        device_label = label or part_id
        pins = []
        for pin_def in part_def.get('pins', []):
            pins.append(Pin(
                id=str(uuid.uuid4()),
                x=pin_def.get('x', 0.0),
                y=pin_def.get('y', 0.0),
                label=pin_def.get('label', pin_def.get('id', '')),
                signal=pin_def.get('signal', ''),
                device_id=device_id,
            ))

        internal_routing = {}
        for route in part_def.get('internal_routes', []):
            route_type = route.get('type', 'common')
            if route_type == 'common':
                route_pin_ids = route.get('pins', [])
                # Map library pin ids to new UUIDs
                lib_to_uuid = {}
                for pin, pin_d in zip(pins, part_def.get('pins', [])):
                    lib_to_uuid[pin_d.get('id', '')] = pin.id
                mapped_pins = [lib_to_uuid.get(p, p) for p in route_pin_ids]
                if mapped_pins:
                    for p in mapped_pins:
                        internal_routing[p] = mapped_pins

        device = Device(
            id=device_id,
            label=device_label,
            pins=pins,
            library_id=part_id,
            svg_body=part_def.get("svg_body"),
            x=x,
            y=y,
            meta={
                "manufacturer": part_def.get("manufacturer", ""),
                "part_number": part_def.get("part_number", ""),
                "description": part_def.get("description", ""),
                "width_mm": part_def.get("width_mm", 40.0),
                "height_mm": part_def.get("height_mm", 30.0),
            },
            internal_routing=internal_routing,
        )
        if hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(AddDeviceCommand(device))
        else:
            AddDeviceCommand(device).execute()
        return device

    def apply_library_part_to_device(self, device, part_id, data):
        """Apply a saved/edited library part definition onto an existing device.

        Copies ``svg_body``, dimensions and metadata from a parts.yaml-style
        ``data`` dict onto ``device`` and dispatches a ``model_changed`` update
        so the canvas item redraws.  This lives on the API (not the wizard) so
        the UI layer never mutates the model directly.
        """
        if device is None:
            return
        device.library_id = part_id
        if not isinstance(getattr(device, "meta", None), dict):
            device.meta = {}
        device.meta.update(
            {
                "manufacturer": data.get("manufacturer", ""),
                "part_number": data.get("part_number", ""),
                "description": data.get("description", ""),
                "width_mm": data.get("width_mm", device.meta.get("width_mm", 40.0)),
                "height_mm": data.get("height_mm", device.meta.get("height_mm", 30.0)),
                "category": data.get("category", device.meta.get("category", "")),
            }
        )
        if data.get("svg_body"):
            device.svg_body = data["svg_body"]
        try:
            self.dispatch("model_changed", {"action": "update", "item": device})
        except Exception:
            pass

    def delete_library_part(self, part_id):
        """Delete a part definition from the parts library.

        Delegates to :meth:`LibraryManager.delete_part` so the UI layer never
        touches parts.yaml directly.  Returns True if the part was removed.
        """
        from infra.logging import infra_log
        infra_log(f"delete_library_part: part_id={part_id}", level="info")
        try:
            removed = bool(self.library.delete_part(part_id))
        except Exception:
            infra_log(f"delete_library_part failed for '{part_id}'", level="error")
            return False
        if removed:
            try:
                self.dispatch("library_changed", {"part_id": part_id, "removed": True})
            except Exception:
                pass
        return removed

    """
    Main API interface for Talus Trace, responsible for managing devices, pins, wires, bundles, and related operations.
    Provides methods for entity lifecycle management and contract enforcement.
    """
    def add_bundle(self, bundle):
        """
        Add a bundle to the model using AddBundleCommand and push to the undo stack.
        Ensures bundle creation is undoable, emits model_changed, and logs the action.
        This method MUST be used for all bundle creation (UI/dispatcher must not mutate model directly).
        """
        from infra.logging import infra_log
        infra_log(f"add_bundle: id={getattr(bundle, 'id', None)}", level="info")
        from api.commands.bundle import AddBundleCommand
        if hasattr(self, 'context') and hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(AddBundleCommand(bundle, self.context.harness))
        else:
            AddBundleCommand(bundle, self.context.harness).execute()

    def detect_wire_overlaps(self, wire=None):
        """
        Detect groups of wires that share a coincident path segment (a 'common
        section') and are candidates to be upgraded into a bundle.

        Sections already covered by an existing bundle are excluded. When ``wire``
        is given (a Wire model or its id), only groups involving that wire are
        returned — used to prompt right after a wire is drawn.

        Returns a list of :class:`core.logic.OverlapGroup`.
        """
        from core.logic.bundling import find_wire_overlaps
        harness = getattr(self.context, 'harness', None)
        if harness is None:
            return []
        grid_size = 2.0
        try:
            grid_size = max(float(getattr(self.settings, 'grid_size_mm', 2.0)), 0.5)
        except Exception:
            pass
        groups = find_wire_overlaps(
            getattr(harness, 'wires', []),
            grid_size=grid_size,
            existing_bundles=getattr(harness, 'bundles', []),
        )
        if wire is not None:
            wid = getattr(wire, 'id', wire)
            groups = [g for g in groups if wid in g.wire_ids]
        return groups

    def create_bundle_from_overlap(self, group):
        """
        Build a bundle from an :class:`~core.logic.OverlapGroup` and add it via
        :meth:`add_bundle` (undoable). Returns the created Bundle.
        """
        from core.logic.bundling import build_bundle_from_overlap
        bundle = build_bundle_from_overlap(group)
        self.add_bundle(bundle)
        return bundle

    def recompute_auto_bundles(self):
        """
        Reconcile emergent (auto) bundles with the current wire layout.

        Bundles are emergent derived state: this scans wires for shared runs
        (hybrid grid + proximity), then adds bundles for new runs and removes
        auto-bundles whose run no longer exists. Manually created bundles (those
        whose ``meta['auto']`` is falsy) are preserved and excluded from
        re-detection so they are never duplicated.

        Emergent bundles are NOT pushed to the undo stack — they re-derive after
        any wire change (including undo/redo, which dispatches wire events). Only
        ``bundle_added`` / ``bundle_removed`` are emitted, so canvas and the
        project browser stay in sync without polluting undo history.

        Returns a tuple ``(added, removed)`` of Bundle lists.
        """
        if getattr(self, '_recomputing_bundles', False):
            return [], []
        harness = getattr(self.context, 'harness', None)
        if harness is None:
            return [], []
        self._recomputing_bundles = True
        try:
            from core.logic.bundling import (
                find_wire_overlaps,
                build_bundle_from_overlap,
                _segment_key_signature,
            )
            bundles = getattr(harness, 'bundles', [])
            manual = [b for b in bundles if not (getattr(b, 'meta', None) or {}).get('auto')]
            auto = [b for b in bundles if (getattr(b, 'meta', None) or {}).get('auto')]

            grid_size = 2.0
            try:
                grid_size = max(float(getattr(self.settings, 'grid_size_mm', 2.0)), 0.5)
            except Exception:
                pass

            groups = find_wire_overlaps(
                getattr(harness, 'wires', []),
                grid_size=grid_size,
                existing_bundles=manual,
            )
            desired = {_segment_key_signature(g.key): g for g in groups}
            current = {
                _segment_key_signature((getattr(b, 'meta', None) or {}).get('segment_key')): b
                for b in auto
            }

            wire_lookup = {w.id: w for w in getattr(harness, 'wires', [])}

            removed, added = [], []
            for key, bundle in list(current.items()):
                if key not in desired:
                    if bundle in harness.bundles:
                        harness.bundles.remove(bundle)
                    removed.append(bundle)
                    self.dispatch("bundle_removed", bundle)
            for key, group in desired.items():
                if key not in current:
                    bundle = build_bundle_from_overlap(group)
                    bundle.compute_geometry(wire_lookup)
                    harness.bundles.append(bundle)
                    added.append(bundle)
                    self.dispatch("bundle_added", bundle)
                else:
                    # Kept bundle: refresh its routable geometry in case member
                    # wires moved within the same grid key, so the trunk and
                    # breakouts track the current layout.
                    kept = current[key]
                    if kept.compute_geometry(wire_lookup):
                        self.dispatch("bundle_updated", kept)
            return added, removed
        finally:
            self._recomputing_bundles = False

    def delete_bundle(self, bundle):
        """
        Delete a bundle from the model using DeleteBundleCommand and push to the undo stack.
        Ensures bundle deletion is undoable, emits model_changed, and logs the action.
        This method MUST be used for all bundle deletion (UI/dispatcher must not mutate model directly).
        """
        from infra.logging import infra_log
        infra_log(f"delete_bundle: id={getattr(bundle, 'id', None)}", level="info")
        from api.commands.bundle import DeleteBundleCommand
        if hasattr(self, 'context') and hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(DeleteBundleCommand(bundle, self.context.harness))
        else:
            DeleteBundleCommand(bundle, self.context.harness).execute()
    def add_device(self, device):
        """
        Add a device to the model using AddDeviceCommand and push to the undo stack.
        Ensures device creation is undoable, emits model_changed, and logs the action.
        This method MUST be used for all device creation (UI/dispatcher must not mutate model directly).
        """
        from infra.logging import infra_log
        infra_log(f"add_device: id={getattr(device, 'id', None)}", level="info")
        from api.commands.device import AddDeviceCommand
        if hasattr(self, 'context') and hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(AddDeviceCommand(device))
        else:
            # Fallback: execute directly (should not happen in production)
            AddDeviceCommand(device).execute()
    # --- UI Command API Stubs ---
    def new_file(self):
        """Stub for file.new UI command."""
        pass

    def open_file(self):
        """Stub for file.open UI command."""
        pass

    def save_file(self):
        """Stub for file.save UI command."""
        pass

    def export_bom(self):
        """Stub for file.export_bom UI command."""
        pass

    def export_wirelist(self):
        """Stub for file.export_wirelist UI command."""
        pass

    def exit_app(self):
        """Stub for file.exit UI command."""
        pass

    def undo(self):
        """Stub for edit.undo UI command."""
        pass

    def redo(self):
        """Stub for edit.redo UI command."""
        pass

    def open_settings(self):
        """Stub for edit.settings UI command."""
        pass

    def set_theme(self):
        """Stub for edit.theme UI command."""
        pass

    def move_tool(self):
        """Stub for tool.move UI command."""
        pass

    def add_generic_device(self):
        """Stub for tool.add_generic_device UI command."""
        pass

    def create_device_wizard(self):
        """Stub for device.create_wizard UI command."""
        pass

    def promote_device(self):
        """Stub for device.promote UI command (launches wizard pre-filled from a generic device)."""
        pass

    def measure_tool(self):
        """Activate the measure tool (tool.measure UI command)."""
        self.tool_manager.set_tool("measure")

    def zoom_extents(self):
        """Stub for view.zoom_extents UI command."""
        pass

    def zoom_selected(self):
        """Stub for view.zoom_selected UI command."""
        pass

    def toggle_project_browser(self):
        """Stub for view.toggle_project_browser UI command."""
        pass

    def toggle_property_panel(self):
        """Stub for view.toggle_property_panel UI command."""
        pass

    def toggle_library(self):
        """Stub for view.toggle_library UI command."""
        pass

    def toggle_audit_panel(self):
        """Stub for view.toggle_audit_panel UI command."""
        pass

    def reset_layout(self):
        """Stub for view.reset_layout UI command."""
        pass

    def add_pin(self):
        """Stub for device.add_pin UI command."""
        pass

    def rotate_cw(self):
        """Rotate selected device(s) 90 degrees clockwise using command pattern."""
        from api.commands.device import RotateDeviceCommand
        from core.selection import SelectionManager
        mgr = SelectionManager()
        for device in mgr.selected_models:
            # Only rotate devices
            if hasattr(device, 'rotation'):
                cmd = RotateDeviceCommand(device, 90, context=self.context)
                if hasattr(self.context, 'undo_stack'):
                    self.context.undo_stack.push(cmd)
                else:
                    cmd.execute()
        self.dispatch("model_changed", {"action": "rotate", "items": mgr.selected_models})

    """
    Main API manager for Talus Trace.
    This singleton class provides high-level methods for manipulating the project state, devices, wires, and UI integration. It manages the tool system, event dispatch, undo/redo, and scene item registry.
    """
    def handle_error(self, error):
        """
        Handle an error event. Contract method for error handling action.
        """
        # Stub: Log or process the error as needed
        pass

    def view_history(self):
        """
        View the project or action history. Contract method for history viewing action.
        """
        # Stub: Show or return history as needed
        pass

    def inspect_undo_stack(self):
        """
        Inspect the undo stack. Contract method for undo stack inspection action.
        """
        # Stub: Return or print undo stack state
        pass
    """
    Main API manager for Talus Trace.

    This singleton class provides high-level methods for manipulating the project state, devices, wires, and UI integration. It manages the tool system, event dispatch, undo/redo, and scene item registry.
    """
    def copy_item(self, item_id):
        """
        Copy the item with the given ID. Contract method for copy action.
        """
        pass

    def paste_item(self):
        """
        Paste the most recently copied item. Contract method for paste action.
        """
        pass

    def import_project(self, path):
        """
        Import a project from the given path. Contract method for import action.
        """
        pass

    def export_project(self, path):
        """
        Export the current project to the given path. Contract method for export action.
        """
        pass

    def log(self, message):
        """
        Log a message. Contract method for logging action.
        """
        pass

    def notify(self, message):
        """
        Send a notification with the given message. Contract method for notification action.
        """
        pass

    def print_project(self, path):
        """
        Print the current project to the given path. Contract method for print action.
        """
        pass

    def recover(self):
        """
        Recover the project/session. Contract method for recovery action.
        """
        pass

    def inspect_redo_stack(self):
        """
        Inspect the redo stack. Contract method for redo stack inspection action.
        """
        pass

    def save_project(self, path):
        """
        Save the current project to the given path. Contract method for save action.
        """
        pass

    def restore_session(self):
        """
        Restore the previous session. Contract method for session restore action.
        """
        pass

    def update_settings(self, settings):
        """
        Update application settings. Contract method for settings action.
        """
        pass

    def set_theme(self, theme_name):
        """
        Set the application theme. Contract method for theme switch action.
        """
        pass

    def update_user_profile(self, profile):
        """
        Update the user profile. Contract method for user profile update action.
        """
        pass
    def autosave(self):
        """
        Trigger autosave logic for the current project/session.
        This method should be called by the autosave action and is required for contract compliance.
        """
        # TODO: Implement autosave logic (e.g., save to temp file, emit event, etc.)
        pass

    def backup(self):
        """
        Trigger backup logic for the current project/session.
        This method should be called by the backup action and is required for contract compliance.
        """
        # TODO: Implement backup logic (e.g., save backup file, emit event, etc.)
        pass
    """
    Main API manager for Talus Trace.

    This singleton class provides high-level methods for manipulating the project state, devices, wires, and UI integration. It manages the tool system, event dispatch, undo/redo, and scene item registry.
    """
    def handle_drop(self, event):
        """Handle drop events for the canvas, supporting library:// device insertion."""
        # Only handle QDropEvent with text starting with library://
        mime = event.mimeData() if hasattr(event, 'mimeData') else None
        if not mime or not mime.hasText():
            return
        text = mime.text()
        if not text.startswith("library://"):
            return
        part_id = text[len("library://"):]
        # Get part definition from library
        part_def = None
        if hasattr(self, 'library') and self.library:
            parts = self.library.get_parts()
            part_def = parts.get(part_id)
        if not part_def:
            return
        # Create device model and add to harness
        Device = self._get_device_model_class()
        # Get drop position in scene coordinates and snap to grid
        pos = event.position() if hasattr(event, 'position') else event.pos() if hasattr(event, 'pos') else None
        x, y = 0.0, 0.0
        if pos is not None:
            x, y = self._event_pos_to_scene(pos)
        if hasattr(self, 'settings') and hasattr(self.settings, 'snap'):
            x = self.settings.snap(x)
            y = self.settings.snap(y)
        device = self.create_device_from_part(part_id, x=x, y=y)
        # Optionally, trigger scene update if needed
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.load_harness(self.context.harness)

    def _event_pos_to_scene(self, pos):
        """Convert a drop event position (viewport pixels) to scene coordinates.

        Qt drop events report the cursor in *viewport* pixels.  Those must be
        mapped through the view transform to land in scene (mm) space so the
        dropped device appears where the ghost preview was shown — even after
        the user has panned or zoomed.  Falls back to the raw coordinates when
        no view is available (e.g. some headless tests).
        """
        view = getattr(self, 'view', None)
        if view is not None and hasattr(view, 'mapToScene'):
            try:
                pt = pos.toPoint() if hasattr(pos, 'toPoint') else pos
                scene_pt = view.mapToScene(pt)
                return float(scene_pt.x()), float(scene_pt.y())
            except Exception:
                pass
        try:
            return float(pos.x()), float(pos.y())
        except Exception:
            return 0.0, 0.0

    def make_drag_ghost_device(self, mime_text):
        """Build an unattached Device model for a drag preview ghost.

        Parses a ``library://<part_id>`` mime string, looks up the part, and
        returns a :class:`Device` populated with the part's ``svg_body`` and
        physical dimensions.  The device is NOT added to the harness — it is a
        throwaway model the view wraps in a ghost :class:`DeviceItem` while the
        drag is in flight.  Returns ``None`` when the mime is not a library
        reference or the part is unknown.
        """
        if not mime_text or not mime_text.startswith("library://"):
            return None
        part_id = mime_text[len("library://"):]
        part_def = None
        if getattr(self, 'library', None):
            part_def = self.library.get_parts().get(part_id)
        if not part_def:
            return None
        from core.device import Device
        import uuid
        return Device(
            id=str(uuid.uuid4()),
            label=part_id,
            library_id=part_id,
            svg_body=part_def.get("svg_body"),
            meta={
                "width_mm": part_def.get("width_mm", 40.0),
                "height_mm": part_def.get("height_mm", 30.0),
            },
        )

    def _get_device_model_class(self):
        """
        Helper to get the Device model class.
        Returns the Device class from core.device, or a minimal fallback if import fails.
        """
        try:
            from core.device import Device
            return Device
        except ImportError:
            # Fallback: create a minimal Device class
            return lambda **kwargs: type('Device', (), kwargs)()
        
    def get_selection(self):
        """Get current selection IDs from SelectionManager (API facade for InputSystem)."""
        from core.selection import SelectionManager
        return SelectionManager().current_selection_ids

    def handle_drag_enter(self, event):
        """
        Validate drag enter event and return True if acceptable, False otherwise.
        API decides acceptance based on mime format, not the View.
        """
        mime = event.mimeData() if hasattr(event, 'mimeData') else None
        if mime and mime.hasText() and mime.text().startswith("library://"):
            return True
        return False

    def move_device(self, target_or_id, new_x, new_y, commit=False):
        """
        Move a device or scene item. If commit=True, push MoveCommand to undo stack; else, update model and dispatch only.
        If commit is False, update model and dispatch for real-time feedback (drag).
        If commit is True, push MoveCommand for undo/redo (on drag finish).
        """
        import logging
        logging.debug(f"[APIManager.move_device] target_or_id={target_or_id}, new_x={new_x}, new_y={new_y}, commit={commit}")
        from api.commands.move import MoveCommand
        from core.device import Device
        from core.pin import Pin
        device = None
        scene_item = None
        
        # Resolve target_or_id to device and scene_item
        if hasattr(target_or_id, 'model'):
            # It's a scene item (has .model attribute)
            scene_item = target_or_id
            device = getattr(scene_item, 'model', None)
        elif isinstance(target_or_id, (Device, Pin)):
            # It's a Device or Pin object directly
            device = target_or_id
            # Try to get scene item from registry
            scene_item = self.get_scene_item(device.id) if hasattr(device, 'id') else None
        else:
            # It's a device ID (string)
            device_id = target_or_id
            for dev in getattr(self.context.harness, 'devices', []):
                if hasattr(dev, 'id') and dev.id == device_id:
                    device = dev
                    break
            # Try to get scene item from registry
            scene_item = self.get_scene_item(device_id)
            
        if device is None:
            return
        if commit:
            # Use the original drag start position for undo, if available
            old_x, old_y = None, None
            if hasattr(scene_item, '_drag_initial_pos'):
                old_x, old_y = scene_item._drag_initial_pos
            else:
                old_x, old_y = getattr(device, 'x', 0.0), getattr(device, 'y', 0.0)
            target = scene_item if scene_item is not None else device
            if scene_item is None and hasattr(device, 'mock_item'):
                target = getattr(device, 'mock_item')
            cmd = MoveCommand(target, (old_x, old_y), (new_x, new_y))
            if hasattr(self.context, 'undo_stack'):
                self.context.undo_stack.push(cmd)
            else:
                cmd.execute()
        else:
            # Directly update model and scene item for real-time feedback.
            # Skip the full dispatch cycle to avoid stuttering during drag.
            device.x = new_x
            device.y = new_y
            if scene_item is None:
                scene_item = self.get_scene_item(getattr(device, 'id', None))
            if scene_item is not None and hasattr(scene_item, 'setPos'):
                scene_item.setPos(new_x, new_y)
            # Update connected wire endpoints during drag
            self._update_connected_wires(device)

    def _update_connected_wires(self, moved_item):
        """Update wire endpoints connected to a moved device or pin."""
        from core.pin import Pin
        from PySide6.QtCore import QPointF
        harness = getattr(self.context, 'harness', None)
        if not harness:
            return
        wires = getattr(harness, 'wires', [])
        if not wires:
            return

        # Determine which device/pin IDs are affected
        if isinstance(moved_item, Pin):
            # Moving a single pin — find its device for scene position calculation
            affected_pin_ids = {moved_item.id}
            device_id = getattr(moved_item, 'device_id', None)
            affected_device_ids = {device_id} if device_id else set()
        else:
            # Moving a device — all its pins are affected
            device_id = getattr(moved_item, 'id', None)
            affected_device_ids = {device_id} if device_id else set()
            affected_pin_ids = set()
            for pin in getattr(moved_item, 'pins', []):
                affected_pin_ids.add(pin.id)

        for wire in wires:
            if not getattr(wire, 'path_nodes', None) or len(wire.path_nodes) < 2:
                continue
            updated = False
            # Check from-endpoint
            if wire.from_pin in affected_pin_ids or wire.from_conn in affected_device_ids:
                pos = self._resolve_pin_scene_pos(wire.from_pin, wire.from_conn)
                if pos is not None:
                    wire.path_nodes[0] = [pos.x(), pos.y()]
                    updated = True
            # Check to-endpoint
            if wire.to_pin in affected_pin_ids or wire.to_conn in affected_device_ids:
                pos = self._resolve_pin_scene_pos(wire.to_pin, wire.to_conn)
                if pos is not None:
                    wire.path_nodes[-1] = [pos.x(), pos.y()]
                    updated = True
            if updated:
                # Update the wire scene item directly for real-time feedback
                # (avoids full dispatch cycle during drag for performance)
                wire_scene_item = self.get_scene_item(getattr(wire, 'id', None))
                if wire_scene_item is not None and hasattr(wire_scene_item, 'update_from_model'):
                    wire_scene_item.update_from_model()

    def _resolve_pin_scene_pos(self, pin_id, device_id):
        """Resolve a pin's absolute scene position from model coordinates.

        Uses the PinItem's mapToScene when available so that the device
        rotation transform is respected.  Falls back to manual rotation
        math when no scene item is registered.
        """
        from PySide6.QtCore import QPointF
        import math
        # Fast path: use the scene item's transform (handles rotation)
        pin_item = self.get_scene_item(pin_id)
        if pin_item is not None and hasattr(pin_item, 'mapToScene'):
            try:
                return pin_item.mapToScene(0.0, 0.0)
            except RuntimeError:
                pass
        # Fallback: manual calculation with rotation
        harness = self.context.harness
        device = None
        for dev in getattr(harness, 'devices', []):
            if dev.id == device_id:
                device = dev
                break
        if device is None:
            return None
        pin = None
        for p in getattr(device, 'pins', []):
            if p.id == pin_id:
                pin = p
                break
        if pin is None:
            return None
        # Rotate pin's local offset around the device's transform origin
        rotation = getattr(device, 'rotation', 0.0)
        ox = device.meta.get('width_mm', 40.0) / 2.0
        oy = device.meta.get('height_mm', 30.0) / 2.0
        lx = pin.x - ox
        ly = pin.y - oy
        rad = math.radians(rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        rx = lx * cos_r - ly * sin_r + ox
        ry = lx * sin_r + ly * cos_r + oy
        return QPointF(round(device.x + rx, 4), round(device.y + ry, 4))

    def open_context_menu(self, event, item=None, menu_type=None):
        """
        Open a context menu at the event location, dispatching a 'context_menu' event.
        Handles both device and canvas context menus, and supports headless/test mode.
        """
        view = getattr(self, 'main_window', None)
        if not view:
            event.accept()
            return
        if hasattr(view, 'context_menu_manager'):
            view.context_menu_manager.show_context_menu(menu_type=menu_type, item=item, event=event, parent=None)
        event.accept()

    def deselect_all(self):
        """Clears all selection for SelectTool compatibility."""
        self.clear_selection()
    def add_wire(self, wire):
        """
        Add a wire to the model using AddWireCommand and push to the undo stack.
        Ensures wire creation is undoable, emits model_changed, and logs the action.
        This method MUST be used for all wire creation (UI/dispatcher must not mutate model directly).
        The API must not generate or mutate IDs; this is handled by the infra/model layer.
        """
        from infra.logging import infra_log
        infra_log(f"add_wire: id={getattr(wire, 'id', None)} from={getattr(wire, 'from_conn', None)} to={getattr(wire, 'to_conn', None)}", level="info")
        from api.commands.device import AddWireCommand
        self.context.undo_stack.push(AddWireCommand(wire))

    def delete_wire(self, wire):
        """
        Delete a wire from the model using DeleteWireCommand and push to the undo stack.
        Ensures wire deletion is undoable, emits model_changed, and logs the action.
        This method MUST be used for all wire deletion (UI/dispatcher must not mutate model directly).
        """
        from infra.logging import infra_log
        infra_log(f"delete_wire: id={getattr(wire, 'id', None)}", level="info")
        from api.commands.device import DeleteWireCommand
        if hasattr(self, 'context') and hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(DeleteWireCommand(wire, context=self.context))
        else:
            DeleteWireCommand(wire, context=self.context).execute()

    @classmethod
    def reset(cls):
        """Reset the singleton instance (for test compatibility)."""
        cls._instance = None

    def move_segment(self, wire, start_idx, end_idx, dx, dy):
        """Move a wire segment by delta values (dx, dy) via the undo stack."""
        from tools.segment_move_tool import MoveSegmentCommand
        # Pass delta values to the command
        cmd = MoveSegmentCommand(wire, start_idx, end_idx, dx, dy, self)
        self.context.undo_stack.push(cmd)

    def add_elbow(self, wire, insert_idx, pos):
        """Add an elbow to a wire at the given index and position."""
        from tools.elbow_commands import AddElbowCommand
        cmd = AddElbowCommand(wire, insert_idx, pos)
        self.context.undo_stack.push(cmd)

    def remove_elbow(self, wire, index):
        """Remove an elbow from a wire at the given index."""
        from tools.elbow_commands import DeleteElbowCommand
        cmd = DeleteElbowCommand(wire, index)
        self.context.undo_stack.push(cmd)

    def move_elbow(self, wire, index, new_pos):
        """Move an elbow to a new position."""
        from tools.elbow_move_tool import MoveElbowCommand
        # Find old_pos for undo
        old_pos = wire.path_nodes[index][:] if 0 <= index < len(wire.path_nodes) else None
        cmd = MoveElbowCommand(wire, index, old_pos, new_pos)
        self.context.undo_stack.push(cmd)
    _instance = None

    def select(self, ids, tool_name=None, additive=False):
        """Selects items by ID, updates SelectionManager, and broadcasts selection_changed.
        If additive is True, adds to current selection set; otherwise, replaces selection.
        """
        from core.selection import SelectionManager
        # Find models by ID from context (devices, wires, etc.)
        models = []
        device_dicts = []
        harness = self.context.harness
        remaining_ids = set(ids)
        for dev in getattr(harness, 'devices', []):
            if hasattr(dev, 'id') and dev.id in remaining_ids:
                models.append(dev)
                device_dicts.append(dev.to_dict())
                remaining_ids.discard(dev.id)
        for wire in getattr(harness, 'wires', []):
            if hasattr(wire, 'id') and wire.id in remaining_ids:
                models.append(wire)
                remaining_ids.discard(wire.id)
        # Search pins inside devices for any remaining unresolved IDs
        if remaining_ids:
            for dev in getattr(harness, 'devices', []):
                for pin in getattr(dev, 'pins', []):
                    if hasattr(pin, 'id') and pin.id in remaining_ids:
                        models.append(pin)
                        remaining_ids.discard(pin.id)
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # ...removed debug print...
        mgr = SelectionManager()
        if additive:
            # Union of current selection and new models, preserving order and uniqueness
            current = mgr.selected_models if hasattr(mgr, 'selected_models') else []
            # Only add models not already selected
            new_models = [m for m in models if m not in current]
            final_selection = current + new_models
            mgr.set_selection(final_selection)
        else:
            mgr.set_selection(models)
        # If only one device is selected, include its dict for UI
        selection_payload = {"selection": mgr.selected_models, "tool": tool_name}
        if len(device_dicts) == 1:
            selection_payload["device_dict"] = device_dicts[0]
        self.dispatch("selection_changed", selection_payload)

    def deselect(self, ids, tool_name=None):
        """
        Deselects items by ID, updates SelectionManager, and broadcasts selection_changed.
        """
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # ...removed debug print...
        """Deselects items by ID, updates SelectionManager, and broadcasts selection_changed."""
        from core.selection import SelectionManager
        mgr = SelectionManager()
        models = [m for m in mgr.selected_models if hasattr(m, 'id') and m.id not in ids]
        mgr.set_selection(models)
        self.dispatch("selection_changed", {"selection": models, "tool": tool_name})

    def clear_selection(self, tool_name=None):
        """
        Clears selection, updates SelectionManager, and broadcasts selection_changed.
        """
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # ...removed debug print...
        """Clears selection, updates SelectionManager, and broadcasts selection_changed."""
        from core.selection import SelectionManager
        SelectionManager().clear_selection()
        self.dispatch("selection_changed", {"selection": [], "tool": tool_name})

    def snap_to_grid(self, x, y=None):
        """Snaps x (and optionally y) to the grid size from settings."""
        grid = getattr(self.settings, 'grid_size_mm', 5.0)
        if y is None:
            return round(x / grid) * grid
        return round(x / grid) * grid, round(y / grid) * grid

    @classmethod
    def get_instance(cls, context=None):
        """
        Get the singleton instance of APIManager, optionally injecting a new context.
        """
        if cls._instance is None:
            cls._instance = cls(context=context)
        elif context is not None:
            # If a context is provided and instance exists, update its context (for test injection)
            cls._instance.context = context
        return cls._instance

    def __init__(self, context=None):
        """
        Initialize the APIManager singleton, setting up settings, context, library, tools, and service layer.
        Raises an exception if an instance already exists (unless reset() was called).
        """
        global Context
        if Context is None:
            from infra.context import Context
        # Allow re-instantiation if reset() was called
        if APIManager._instance is not None:
            raise Exception("This class is a singleton! Call APIManager.reset() before creating a new instance in tests.")
        APIManager._instance = self

        # --- PHASE 1: CORE FOUNDATION ---
        self.settings = SystemSettings()  # Physics (Grid/Units)
        self.context = context if context is not None else Context()  # Session Data
        self.library = LibraryManager()   # Part Database

        # --- PHASE 2: SERVICE LAYER ---
        self.input_system = None  # Created by UI layer (ui/app.py)
        self.tool_manager = None
        self.main_window = None 

        # --- PHASE 3: REGISTRATION (The Fix) ---
        # We must import these modules so their @register_action decorators run.
        import api.commands.file
        import api.commands.edit
        import api.commands.view
        import api.commands.tools
        import api.commands.device

        # Initialize Tools
        from api.tool_manager import ToolManager
        from tools.select_tool import SelectTool
        from tools.wire_tool import WireTool
        from tools.placement_tool import PlacementTool
        from tools.move_tool import MoveTool
        from tools.elbow_move_tool import ElbowMoveTool
        from tools.segment_move_tool import SegmentMoveTool
        from tools.measure_tool import MeasureTool

        self.tool_manager = ToolManager()
        self.tool_manager.register_tool("select", SelectTool())
        self.tool_manager.register_tool("wire", WireTool())
        self.tool_manager.register_tool("placement", PlacementTool())
        self.tool_manager.register_tool("move", MoveTool())
        self.tool_manager.register_tool("elbow_move", ElbowMoveTool())
        self.tool_manager.register_tool("segment_move", SegmentMoveTool())
        self.tool_manager.register_tool("measure", MeasureTool())
        self.tool_manager.set_tool("select")  # Default active tool

    # --- Scene Object Registry ---
    # ── Visibility & visibility groups ───────────────────────────────
    def find_item_by_id(self, item_id):
        """
        Resolve a top-level harness item (device, wire, or bundle) by its ID.
        Args:
            item_id (str): The UUID of the item to find.
        Returns:
            The matching model object, or None if not found.
        """
        harness = getattr(self.context, 'harness', None)
        if harness is None:
            return None
        for dev in getattr(harness, 'devices', []):
            if getattr(dev, 'id', None) == item_id:
                return dev
        for wire in getattr(harness, 'wires', []):
            if getattr(wire, 'id', None) == item_id:
                return wire
        for bundle in getattr(harness, 'bundles', []):
            if getattr(bundle, 'id', None) == item_id:
                return bundle
        return None

    def set_item_visibility(self, item_ids, visible):
        """
        Set the visibility of one or more items (devices, wires, bundles) via the
        command pattern so the change is undoable and persisted with the model.
        Args:
            item_ids (str | list[str]): One ID or a list of IDs to update.
            visible (bool): Target visibility.
        """
        if isinstance(item_ids, str):
            item_ids = [item_ids]
        item_ids = [i for i in item_ids if i]
        if not item_ids:
            return
        from api.commands.visibility import SetVisibilityCommand
        cmd = SetVisibilityCommand(item_ids, visible)
        if hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(cmd)
        else:
            cmd.execute()

    def _visibility_groups_ref(self):
        """Return the live visibility-groups list stored in harness.meta."""
        harness = getattr(self.context, 'harness', None)
        if harness is None:
            return []
        if getattr(harness, 'meta', None) is None:
            harness.meta = {}
        return harness.meta.setdefault('visibility_groups', [])

    def get_visibility_groups(self):
        """
        Return the list of user-defined visibility groups.
        Each group is a dict: {"id": str, "name": str, "members": [item_id, ...]}.
        """
        import copy
        return copy.deepcopy(self._visibility_groups_ref())

    def _push_groups(self, new_groups, description):
        """Push a SetVisibilityGroupsCommand to replace the groups definition."""
        from api.commands.visibility import SetVisibilityGroupsCommand
        cmd = SetVisibilityGroupsCommand(new_groups, description)
        if hasattr(self.context, 'undo_stack'):
            self.context.undo_stack.push(cmd)
        else:
            cmd.execute()

    def create_visibility_group(self, name, member_ids=None):
        """
        Create a new, undoable visibility group and return its generated ID.
        Args:
            name (str): Display name for the group.
            member_ids (list[str] | None): Optional initial member item IDs.
        Returns:
            str: The new group's ID.
        """
        import uuid
        groups = self.get_visibility_groups()
        group_id = str(uuid.uuid4())
        groups.append({
            "id": group_id,
            "name": name,
            "members": list(member_ids or []),
        })
        self._push_groups(groups, "Create Group")
        return group_id

    def rename_visibility_group(self, group_id, name):
        """Rename a visibility group (undoable)."""
        groups = self.get_visibility_groups()
        for g in groups:
            if g.get("id") == group_id:
                g["name"] = name
                break
        else:
            return
        self._push_groups(groups, "Rename Group")

    def delete_visibility_group(self, group_id):
        """Delete a visibility group (undoable). Does not affect item visibility."""
        groups = [g for g in self.get_visibility_groups() if g.get("id") != group_id]
        self._push_groups(groups, "Delete Group")

    def set_group_members(self, group_id, member_ids):
        """Replace the member list of a visibility group (undoable)."""
        groups = self.get_visibility_groups()
        for g in groups:
            if g.get("id") == group_id:
                g["members"] = list(member_ids)
                break
        else:
            return
        self._push_groups(groups, "Edit Group Members")

    def add_items_to_group(self, group_id, item_ids):
        """Add one or more items to a visibility group (undoable), de-duplicated."""
        if isinstance(item_ids, str):
            item_ids = [item_ids]
        groups = self.get_visibility_groups()
        for g in groups:
            if g.get("id") == group_id:
                members = list(g.get("members", []))
                for i in item_ids:
                    if i and i not in members:
                        members.append(i)
                g["members"] = members
                break
        else:
            return
        self._push_groups(groups, "Add to Group")

    def remove_items_from_group(self, group_id, item_ids):
        """Remove one or more items from a visibility group (undoable)."""
        if isinstance(item_ids, str):
            item_ids = [item_ids]
        remove = set(item_ids)
        groups = self.get_visibility_groups()
        for g in groups:
            if g.get("id") == group_id:
                g["members"] = [m for m in g.get("members", []) if m not in remove]
                break
        else:
            return
        self._push_groups(groups, "Remove from Group")

    def set_group_visibility(self, group_id, visible):
        """
        Set the visibility of every member of a group (undoable, batched).
        Args:
            group_id (str): The group whose members to toggle.
            visible (bool): Target visibility for all members.
        """
        for g in self._visibility_groups_ref():
            if g.get("id") == group_id:
                self.set_item_visibility(list(g.get("members", [])), visible)
                return

    def register_scene_item(self, model_id, item):
        """
        Register a scene item (UI object) with a model ID for lookup and selection.
        """
        if not hasattr(self, '_scene_registry'):
            self._scene_registry = {}
        self._scene_registry[model_id] = item

    def unregister_scene_item(self, model_id):
        """
        Unregister a scene item by its model ID.
        """
        if hasattr(self, '_scene_registry') and model_id in self._scene_registry:
            del self._scene_registry[model_id]

    def get_scene_item(self, model_id):
        """
        Retrieve a registered scene item by its model ID.
        Returns None if not found.
        """
        if hasattr(self, '_scene_registry'):
            return self._scene_registry.get(model_id)
        return None

    def find_pin_item(self, device_id, pin_id):
        """
        Look up a PinItem by device_id and pin_id in the scene registry.
        Returns the item if found, else None.
        """
        # Look up PinItem by device_id and pin_id
        if not hasattr(self, '_scene_registry'):
            return None
        for item in self._scene_registry.values():
            # PinItem: has .model with .device_id and .id
            model = getattr(item, 'model', None)
            if model and getattr(model, 'device_id', None) == device_id and getattr(model, 'id', None) == pin_id:
                return item
        return None
    def subscribe(self, arg1, arg2=None):
        """
        Subscribe to events. Handles flexible signatures:
        1. subscribe(event_type: str, callback: callable) -> Standard
        2. subscribe(callback: callable) -> defaults to "state_changed"
        """
        event_type = "state_changed"
        callback = None

        if isinstance(arg1, str):
            # Case 1: subscribe("event_name", callback)
            event_type = arg1
            callback = arg2
        elif callable(arg1):
            # Case 2: subscribe(callback, [event_type]) - Legacy/Test compat
            callback = arg1
            if arg2 is not None:
                event_type = arg2
        else:
            # Fallback (mostly for robustness)
            callback = arg1
            
        if callback:
            self.context.observer.subscribe(event_type, callback)

    def dispatch(self, event_type, data=None):
        """
        Dispatch an event to all observers, or route through the dispatcher if registered.
        Always dispatch 'state_changed' for compatibility.
        For 'model_changed' and 'selection_changed', always dispatch directly to observers (never via dispatcher),
        so the UI can update the scene and selection.
        """
        from infra.logging import infra_log
        if data is None:
            data = {}
        infra_log(f"[APIManager] dispatch called: event_type={event_type}, data={data}", level="debug")
        # Always dispatch these events directly to observers for UI contract
        if event_type in ("model_changed", "selection_changed"):
            self.context.observer.dispatch(event_type, data)
            if event_type != "state_changed":
                self.context.observer.dispatch("state_changed", data)
            return
        try:
            from dispatcher import registry, dispatch_action
        except ImportError:
            registry = None
            dispatch_action = None
        # Log dispatcher registry state and event_type
        if registry:
            infra_log(f"[APIManager] dispatcher registry keys at dispatch: {list(registry.keys())}", level="debug")
            infra_log(f"[APIManager] event_type at dispatch: {event_type}", level="debug")
        # If event_type is a registered dispatcher action, use dispatcher
        if registry and event_type in registry:
            infra_log(f"[APIManager] dispatch routing to dispatcher for action: {event_type}", level="debug")
            return dispatch_action(event_type, data)
        # Otherwise, dispatch to observers as before
        self.context.observer.dispatch(event_type, data)
        # Always also dispatch 'state_changed' for observer notification compatibility
        if event_type != "state_changed":
            self.context.observer.dispatch("state_changed", data)