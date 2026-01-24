from infra.harness_serializer import HarnessSerializer
from core.bundle import Bundle
from core.wire import Wire
from tests.infra.factories import make_wire, make_bundle, make_segment_membership

# Dummy harness-like structure for testing
class DummyHarness:
    def __init__(self, bundles=None, wires=None):
        self.bundles = bundles or []
        self.wires = wires or []

    def to_dict(self):
        return {
            'bundles': [b.to_dict() for b in self.bundles],
            'wires': [w.to_dict() for w in self.wires],
        }

    @classmethod
    def from_dict(cls, data):
        bundles = [Bundle.from_dict(b) for b in data.get('bundles', [])]
        wires = [Wire.from_dict(w) for w in data.get('wires', [])]
        return cls(bundles, wires)

def test_bundle_yaml_roundtrip():
    w = make_wire()
    seg = make_segment_membership(wire_id=w.id, start_node=0, end_node=1)
    bundle = make_bundle(wire_ids=[w.id], segments=[seg], meta={"foo": "bar"})
    harness = DummyHarness(bundles=[bundle], wires=[w])

    # Serialize to YAML
    yaml_str = HarnessSerializer.to_yaml(harness.to_dict())
    assert 'bundles' in yaml_str and 'segment_memberships' in yaml_str

    # Deserialize from YAML
    data = HarnessSerializer.from_yaml(yaml_str)
    loaded = DummyHarness.from_dict(data)
    assert loaded.bundles[0].wire_ids == [w.id]
    assert loaded.bundles[0].segments[0].wire_id == w.id
    assert loaded.bundles[0].meta["foo"] == "bar"
    assert loaded.wires[0].id == w.id

def test_wire_segment_membership_yaml():
    w = make_wire()
    seg = make_segment_membership(wire_id=w.id, start_node=0, end_node=2)
    w.segment_memberships.append(seg)
    harness = DummyHarness(wires=[w])
    yaml_str = HarnessSerializer.to_yaml(harness.to_dict())
    data = HarnessSerializer.from_yaml(yaml_str)
    loaded = DummyHarness.from_dict(data)
    assert loaded.wires[0].segment_memberships[0].wire_id == w.id
