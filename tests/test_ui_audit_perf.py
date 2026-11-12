"""Regression tests for audit performance on model changes.

The audit engine previously re-read its rules YAML from disk and ran a full
audit synchronously for every ``model_changed`` event, which froze the UI while
editing. These tests lock in the debounced/coalesced behavior and rule caching.
"""
from unittest.mock import MagicMock

from ui.panels.audit import AuditPanel
from api.manager import APIManager
from infra import audit as audit_module


def test_model_changed_does_not_run_audit_synchronously(qtbot):
    APIManager._instance = None
    APIManager.get_instance()
    panel = AuditPanel()
    qtbot.add_widget(panel)

    panel.run_audit = MagicMock()

    # A single model change should schedule, not immediately run, the audit.
    panel._on_model_changed({"action": "update"})
    assert panel.run_audit.call_count == 0
    assert panel._audit_timer.isActive()

    # Rapid successive changes must still coalesce into one deferred run.
    panel._on_model_changed({"action": "update"})
    panel._on_model_changed({"action": "update"})
    qtbot.waitUntil(lambda: panel.run_audit.call_count == 1, timeout=1000)
    assert panel.run_audit.call_count == 1


def test_load_rules_from_yaml_is_cached():
    audit_module._RULES_CACHE.clear()
    first = audit_module.load_rules_from_yaml()
    second = audit_module.load_rules_from_yaml()
    # Same underlying cached list object (no re-parse from disk).
    assert first is second
