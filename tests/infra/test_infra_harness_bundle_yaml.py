from infra.persistence import YAMLPersistence
from tests.infra.factories import make_wire, make_bundle, make_segment_membership

def test_harness_bundle_yaml_roundtrip(tmp_path):
    w = make_wire()
    seg = make_segment_membership(wire_id=w.id, start_node=0, end_node=1)
    bundle = make_bundle(wire_ids=[w.id], segments=[seg], meta={"foo": "bar"})
    from core.harness import Harness
    harness = Harness(wires=[w])
    harness.bundles = [bundle]

    file_path = tmp_path / "harness.yaml"
    YAMLPersistence.save(harness, file_path)
    loaded = YAMLPersistence.load(file_path)

    assert loaded.bundles[0].wire_ids == [w.id]
    assert loaded.bundles[0].segments[0].wire_id == w.id
    assert loaded.bundles[0].meta["foo"] == "bar"
    assert loaded.wires[0].id == w.id

def test_harness_wire_segment_membership_yaml(tmp_path):
    w = make_wire()
    seg = make_segment_membership(wire_id=w.id, start_node=0, end_node=2)
    w.segment_memberships.append(seg)
    from core.harness import Harness
    harness = Harness(wires=[w])
    file_path = tmp_path / "harness.yaml"
    YAMLPersistence.save(harness, file_path)
    loaded = YAMLPersistence.load(file_path)
    assert loaded.wires[0].segment_memberships[0].wire_id == w.id
