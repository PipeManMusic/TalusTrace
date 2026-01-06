import pytest
from PySide6.QtWidgets import QGraphicsScene
from talustrace.backend.models import TwistedPair

# Import the real TwistedPairItem if available
from talustrace.frontend.twisted_pair import TwistedPairItem

def make_item():
    model = TwistedPair(
        id="tp1",
        node_a=(0.0, 0.0),
        node_b=(100.0, 0.0),
        rotation_a=0,
        rotation_b=0,
        wire_id_1=None,
        wire_id_2=None
    )
    item = TwistedPairItem(model)
    return item

@pytest.fixture
def scene(qtbot):
    s = QGraphicsScene()
    yield s

def test_dual_pin_structure(scene):
    item = make_item()
    scene.addItem(item)
    # Spec: Each anchor should have 2 pins
    assert hasattr(item.anchor_a, 'pins'), "anchor_a should have a 'pins' attribute (list)"
    assert hasattr(item.anchor_b, 'pins'), "anchor_b should have a 'pins' attribute (list)"
    assert isinstance(item.anchor_a.pins, list), "anchor_a.pins should be a list"
    assert isinstance(item.anchor_b.pins, list), "anchor_b.pins should be a list"
    assert len(item.anchor_a.pins) == 2, f"anchor_a.pins should have length 2, got {len(item.anchor_a.pins)}"
    assert len(item.anchor_b.pins) == 2, f"anchor_b.pins should have length 2, got {len(item.anchor_b.pins)}"

def test_signal_assignment_channel_1(scene):
    item = make_item()
    scene.addItem(item)
    # Assign signal to anchor_a pin 0
    item.set_signal(item.anchor_a.pins[0], wire_id="RED_WIRE", color="#FF0000")
    assert item.model.wire_id_1 == "RED_WIRE"
    assert item.model.wire_id_2 is None

def test_signal_assignment_channel_2(scene):
    item = make_item()
    scene.addItem(item)
    # Assign signal to anchor_a pin 1
    item.set_signal(item.anchor_a.pins[1], wire_id="BLACK_WIRE", color="#000000")
    assert item.model.wire_id_2 == "BLACK_WIRE"

def test_propagation_to_other_end(scene):
    item = make_item()
    scene.addItem(item)
    # Assign signal to anchor_a pin 0
    item.set_signal(item.anchor_a.pins[0], wire_id="RED_WIRE", color="#FF0000")
    # For now, just check that anchor_b.pins[0] returns the same wire_id
    assert item.get_signal(item.anchor_b.pins[0]) == "RED_WIRE"
