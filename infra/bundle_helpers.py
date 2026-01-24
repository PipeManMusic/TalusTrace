"""
infra/bundle_helpers.py

Helpers for recursive traversal and operations on nested bundles.
"""
from typing import List, Callable

def flatten_bundles(bundle, get_bundle_by_id: Callable):
    """
    Recursively yields all bundles in the hierarchy, including nested ones.
    get_bundle_by_id: function to resolve a bundle by its id (for nested references)
    """
    yield bundle
    for nested_id in getattr(bundle, 'bundle_ids', []):
        nested = get_bundle_by_id(nested_id)
        if nested:
            yield from flatten_bundles(nested, get_bundle_by_id)

def all_segments(bundle, get_bundle_by_id: Callable):
    """
    Recursively yields all segments from this bundle and nested bundles.
    """
    for seg in getattr(bundle, 'segments', []):
        yield seg
    for nested_id in getattr(bundle, 'bundle_ids', []):
        nested = get_bundle_by_id(nested_id)
        if nested:
            yield from all_segments(nested, get_bundle_by_id)
