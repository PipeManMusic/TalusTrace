import pytest
from core.bundle import Bundle, BundleSegmentMembership

def test_bundle_segment_validation():
    # Valid segment
    seg1 = BundleSegmentMembership(id="uuid-1", wire_id="wire-1", start_node=0, end_node=1)
    seg2 = BundleSegmentMembership(id="uuid-2", wire_id="wire-2", start_node=1, end_node=2)
    bundle = Bundle(id="bundle-1", segments=[seg1, seg2])
    bundle.validate_segments()  # Should not raise

    # Duplicate UUID
    seg3 = BundleSegmentMembership(id="uuid-1", wire_id="wire-3", start_node=2, end_node=3)
    bundle_dup_uuid = Bundle(id="bundle-2", segments=[seg1, seg3])
    with pytest.raises(AssertionError, match="Duplicate segment UUID"):
        bundle_dup_uuid.validate_segments()

    # Duplicate membership
    seg4 = BundleSegmentMembership(id="uuid-3", wire_id="wire-1", start_node=0, end_node=1)
    bundle_dup_key = Bundle(id="bundle-3", segments=[seg1, seg4])
    with pytest.raises(AssertionError, match="Duplicate segment membership"):
        bundle_dup_key.validate_segments()

    # Invalid membership (end_node <= start_node)
    seg5 = BundleSegmentMembership(id="uuid-4", wire_id="wire-4", start_node=2, end_node=2)
    bundle_bad = Bundle(id="bundle-4", segments=[seg5])
    with pytest.raises(AssertionError, match="end_node must be greater than start_node"):
        bundle_bad.validate_segments()
