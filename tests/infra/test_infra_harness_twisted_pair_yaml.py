from core.wire import Wire
from core.harness import Harness
from infra.persistence import YAMLPersistence
from core.bundle import BundleSegmentMembership, Bundle

def test_harness_bundle_twisted_segment_yaml_roundtrip(tmp_path):
    w1 = Wire(from_conn="A", to_conn="B")
    w2 = Wire(from_conn="C", to_conn="D")
    # Create a bundle with both wires, and a twisted segment
    seg = BundleSegmentMembership(wire_id=w1.id, start_node=0, end_node=2, twisted=True, meta={"foo": "bar"})
    bundle = Bundle(wire_ids=[w1.id, w2.id], segments=[seg], meta={"pattern": "custom", "turns_per_meter": 42})
    harness = Harness(wires=[w1, w2], bundles=[bundle])
    file_path = tmp_path / "harness.yaml"
    YAMLPersistence.save(harness, file_path)
    loaded = YAMLPersistence.load(file_path)
    assert len(loaded.bundles) == 1
    loaded_bundle = loaded.bundles[0]
    assert set(loaded_bundle.wire_ids) == {w1.id, w2.id}
    assert loaded_bundle.meta["turns_per_meter"] == 42
    assert loaded_bundle.meta["pattern"] == "custom"
    assert loaded_bundle.segments[0].wire_id == w1.id
    assert loaded_bundle.segments[0].twisted is True
    assert loaded_bundle.segments[0].meta["foo"] == "bar"
