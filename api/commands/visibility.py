"""
Visibility command implementations for Talus Trace.

Provides undoable commands for toggling the visibility of model items
(devices, wires, bundles) and for editing user-defined visibility groups.
Groups are persisted in ``harness.meta['visibility_groups']`` as a list of
dicts: ``{"id": str, "name": str, "members": [item_id, ...]}``.
"""

import copy

from api.manager import APIManager
from infra.undo_stack import BaseCommand

VISIBILITY_GROUPS_META_KEY = "visibility_groups"


class SetVisibilityCommand(BaseCommand):
    """
    Command to set the ``visible`` flag on one or more model items, supporting undo/redo.
    """

    def __init__(self, target_ids, visible):
        """
        Initialize with the item IDs to update and the desired visibility.
        Args:
            target_ids (list[str]): IDs of devices, wires, or bundles.
            visible (bool): Target visibility value.
        """
        super().__init__("Set Visibility")
        self.target_ids = list(target_ids)
        self.new_value = bool(visible)
        self.api = APIManager.get_instance()
        # Captured on execute so undo can restore per-item previous state.
        self._old_values = {}

    def _resolve_targets(self):
        """Return the list of model objects matching ``self.target_ids``."""
        return [self.api.find_item_by_id(i) for i in self.target_ids]

    def execute(self):
        """Apply the visibility value to each target and dispatch updates."""
        self._old_values = {}
        for model in self._resolve_targets():
            if model is None:
                continue
            self._old_values[model.id] = getattr(model, "visible", True)
            model.visible = self.new_value
            self.api.dispatch("model_changed", {"action": "update", "item": model})
        self.api.dispatch("visibility_changed", {"ids": self.target_ids, "visible": self.new_value})

    def undo(self):
        """Restore each target's previous visibility and dispatch updates."""
        for model in self._resolve_targets():
            if model is None:
                continue
            model.visible = self._old_values.get(model.id, True)
            self.api.dispatch("model_changed", {"action": "update", "item": model})
        self.api.dispatch("visibility_changed", {"ids": self.target_ids, "visible": None})


class SetVisibilityGroupsCommand(BaseCommand):
    """
    Command that replaces the entire visibility-groups definition, supporting undo/redo.

    Used for creating, renaming, deleting groups and editing group membership.
    Snapshots the previous group list so undo restores it exactly.
    """

    def __init__(self, new_groups, description="Edit Visibility Groups"):
        """
        Initialize with the new groups list.
        Args:
            new_groups (list[dict]): The replacement visibility-groups definition.
            description (str): Human-readable command description.
        """
        super().__init__(description)
        self.api = APIManager.get_instance()
        self.new_groups = copy.deepcopy(new_groups)
        self._old_groups = None

    def _meta(self):
        """Return the harness meta dict (creating it if absent)."""
        harness = self.api.context.harness
        if getattr(harness, "meta", None) is None:
            harness.meta = {}
        return harness.meta

    def execute(self):
        """Store the new groups list, snapshotting the previous value for undo."""
        meta = self._meta()
        self._old_groups = copy.deepcopy(meta.get(VISIBILITY_GROUPS_META_KEY, []))
        meta[VISIBILITY_GROUPS_META_KEY] = copy.deepcopy(self.new_groups)
        self.api.dispatch("visibility_groups_changed", {"groups": meta[VISIBILITY_GROUPS_META_KEY]})

    def undo(self):
        """Restore the previous groups list."""
        meta = self._meta()
        meta[VISIBILITY_GROUPS_META_KEY] = copy.deepcopy(self._old_groups or [])
        self.api.dispatch("visibility_groups_changed", {"groups": meta[VISIBILITY_GROUPS_META_KEY]})
