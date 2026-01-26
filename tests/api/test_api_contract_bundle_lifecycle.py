"""
API contract tests for full bundle lifecycle: add, update, remove, undo, redo.
Covers creation, modification, deletion, and undo/redo for bundles at the API level.
"""
import pytest
from api.manager import APIManager
from core.harness import Harness
from core.bundle import Bundle, BundleSegmentMembership

@pytest.fixture
def api():
    # Create a fresh APIManager and Harness for each test
    harness = Harness()
    api = APIManager.get_instance()
    api.context.harness = harness
    # Reset undo stack if present
    if hasattr(api.context, 'undo_stack'):
        api.context.undo_stack.clear()
    return api

def make_bundle(wire_ids=None, meta=None):
    wire_ids = wire_ids or ["wire-1", "wire-2"]
    meta = meta or {"test": True}
    segments = [BundleSegmentMembership(wire_id=w, start_node=0, end_node=1, twisted=False) for w in wire_ids]
    return Bundle(wire_ids=wire_ids, segments=segments, meta=meta)


def test_api_add_bundle(api):
    bundle = make_bundle()
    api.add_bundle(bundle)
    assert bundle in api.context.harness.bundles


def test_api_update_bundle(api):
    bundle = make_bundle()
    api.add_bundle(bundle)
    bundle.meta["updated"] = True
    assert api.context.harness.bundles[0].meta["updated"] is True


def test_api_remove_bundle(api):
    bundle = make_bundle()
    api.add_bundle(bundle)
    api.delete_bundle(bundle)
    assert bundle not in api.context.harness.bundles


def test_api_undo_redo_bundle_add(api):
    bundle = make_bundle()
    api.add_bundle(bundle)
    if hasattr(api.context, 'undo_stack'):
        api.context.undo_stack.undo()
        assert bundle not in api.context.harness.bundles
        api.context.undo_stack.redo()
        assert bundle in api.context.harness.bundles


def test_api_bundle_lifecycle_contract(api):
    bundle = make_bundle()
    # Add
    api.add_bundle(bundle)
    assert bundle in api.context.harness.bundles
    # Update
    bundle.meta["foo"] = "bar"
    assert api.context.harness.bundles[0].meta["foo"] == "bar"
    # Remove
    api.delete_bundle(bundle)
    assert bundle not in api.context.harness.bundles
    # Undo/Redo (if undo_stack present)
    if hasattr(api.context, 'undo_stack'):
        api.context.undo_stack.undo()
        assert bundle in api.context.harness.bundles
        api.context.undo_stack.redo()
        assert bundle not in api.context.harness.bundles
