import pytest
from core.wire import Wire, on_wire_split, on_wire_merge, on_wire_serialize

def test_on_wire_split_event():
    wire = Wire()
    wire.path_nodes = [[0, 0], [10, 0]]
    wire.update_segments()
    events = []
    on_wire_split.clear_subscribers()
    def listener(w, old_segment_uuid, new_node, new_uuids):
        events.append((w, old_segment_uuid, new_node, new_uuids))
    on_wire_split.subscribe(listener)
    try:
        seg_uuid = wire.segments[0].id
        new_uuids = wire.split_segment(seg_uuid, [5, 0])
        assert len(events) == 1
        assert events[0][0] is wire
        assert events[0][1] == seg_uuid
        assert events[0][2] == [5, 0]
        assert events[0][3] == new_uuids
    finally:
        on_wire_split.unsubscribe(listener)

def test_on_wire_merge_event():
    wire = Wire()
    # Use 5 nodes to ensure merge does not cause out-of-range
    wire.path_nodes = [[0, 0], [5, 0], [10, 0], [15, 0], [20, 0]]
    wire.update_segments()
    events = []
    on_wire_merge.clear_subscribers()
    def listener(w, left_segment_uuid, merged_uuid):
        events.append((w, left_segment_uuid, merged_uuid))
    on_wire_merge.subscribe(listener)
    try:
        left_uuid = wire.segments[2].id
        merged_uuid = wire.merge_segments(left_uuid)
        assert len(events) == 1
        assert events[0][0] is wire
        assert events[0][1] == left_uuid
        assert events[0][2] == merged_uuid
    finally:
        on_wire_merge.unsubscribe(listener)

def test_on_wire_serialize_event():
    wire = Wire()
    events = []
    on_wire_serialize.clear_subscribers()
    def listener(w, d):
        events.append((w, d))
    on_wire_serialize.subscribe(listener)
    try:
        d = wire.to_dict()
        assert len(events) == 1
        assert events[0][0] is wire
        assert events[0][1] == d
    finally:
        on_wire_serialize.unsubscribe(listener)
