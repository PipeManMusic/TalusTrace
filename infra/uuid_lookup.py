"""
infra/uuid_lookup.py

Helpers for fetching any model/entity by UUID from a harness or flat collection.
"""

def get_by_uuid(harness, uuid):
    """
    Fetch any entity (device, pin, wire, bundle, segment, etc.) by UUID from the harness.
    Returns the object or None if not found.
    """
    # Devices
    for d in getattr(harness, 'devices', []):
        if d.id == uuid:
            return d
        for p in getattr(d, 'pins', []):
            if p.id == uuid:
                return p
    # Wires
    for w in getattr(harness, 'wires', []):
        if w.id == uuid:
            return w
        for seg in getattr(w, 'segments', []):
            if seg.id == uuid:
                return seg
        for sm in getattr(w, 'segment_memberships', []):
            if sm.id == uuid:
                return sm
    # Bundles
    for b in getattr(harness, 'bundles', []):
        if b.id == uuid:
            return b
        for seg in getattr(b, 'segments', []):
            if seg.id == uuid:
                return seg
    return None
