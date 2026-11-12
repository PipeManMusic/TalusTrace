"""
Bundle inference service for Talus Trace.

Wires the emergent-bundle recompute (``APIManager.recompute_auto_bundles``) to
wire lifecycle events so bundles appear/disappear automatically as wires are
added, moved, or deleted — no manual step. This layer only listens for events
and delegates all model mutation to the API; it never touches the model or UI
directly.
"""
from core.wire import Wire

#: Master switch for the bundling feature (emergent detection + trunk rendering).
#: Disabled for now — bundling behavior did not match expectations and will be
#: revisited once a proper spec exists. Flip to ``True`` to re-enable everything
#: (auto-detection service in ``ui/app.py`` and trunk rendering in the canvas).
BUNDLING_ENABLED = False


class BundleInferenceService:
    """Recompute emergent bundles whenever wires change."""

    def __init__(self, api):
        """Subscribe to wire lifecycle events on the given APIManager."""
        self.api = api
        api.subscribe("wire_added", self._on_wire_event)
        api.subscribe("wire_removed", self._on_wire_event)
        api.subscribe("wire_restored", self._on_wire_event)
        api.subscribe("model_changed", self._on_model_changed)

    def _on_wire_event(self, _data=None):
        """Recompute after an explicit wire add/remove/restore."""
        self.api.recompute_auto_bundles()

    def _on_model_changed(self, data):
        """Recompute after a wire path edit (elbow/segment move updates a Wire)."""
        item = data.get("item") if isinstance(data, dict) else None
        if isinstance(item, Wire):
            self.api.recompute_auto_bundles()
