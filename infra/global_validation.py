"""
infra/global_validation.py

Validation for global UUID uniqueness across all model objects in a harness.
"""

def collect_all_uuids(harness) -> set:
    """
    Collect all UUIDs from bundles, wires, devices, pins, segments, etc.
    """
    uuids = set()
    # Devices
    for d in getattr(harness, 'devices', []):
        uuids.add(d.id)
        for p in getattr(d, 'pins', []):
            uuids.add(p.id)
    # Wires
    for w in getattr(harness, 'wires', []):
        uuids.add(w.id)
        for seg in getattr(w, 'segments', []):
            uuids.add(seg.id)
        for sm in getattr(w, 'segment_memberships', []):
            uuids.add(sm.id)
    # Bundles
    for b in getattr(harness, 'bundles', []):
        uuids.add(b.id)
        for seg in getattr(b, 'segments', []):
            uuids.add(seg.id)
    return uuids

def validate_global_uuid_uniqueness(harness):
    """
    Validate that all UUIDs in the harness are globally unique across all model objects.
    Args:
        harness: The harness object containing devices, wires, bundles, etc.
    Raises:
        AssertionError: If duplicate UUIDs are found.
    """
    uuids = list(collect_all_uuids(harness))
    assert len(uuids) == len(set(uuids)), "Global UUIDs must be unique across all model objects!"
