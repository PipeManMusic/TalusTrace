import pytest
from PySide6.QtWidgets import QGraphicsScene
from talustrace.backend.models import TwistedPair
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

def test_initial_orientation(scene):
    item = make_item()
    scene.addItem(item)
    # Pins should be vertical: same X, different Y
    pin0 = item.anchor_a.pins[0].scenePos()
    pin1 = item.anchor_a.pins[1].scenePos()
    assert pin0.x() == pytest.approx(pin1.x()), f"Pins should be vertically aligned (same X): {pin0.x()} vs {pin1.x()}"
    assert pin0.y() != pytest.approx(pin1.y()), f"Pins should have different Y: {pin0.y()} vs {pin1.y()}"

def test_rotate_method_updates_model(scene):
    item = make_item()
    scene.addItem(item)
    item.anchor_a.rotate_90()
    assert item.model.rotation_a == 90, f"rotation_a should be 90 after one rotate_90, got {item.model.rotation_a}"
    assert item.model.rotation_b == 0, f"rotation_b should remain 0, got {item.model.rotation_b}"

def test_rotation_updates_layout(scene):
    item = make_item()
    scene.addItem(item)
    # Initial: vertical
    pin0 = item.anchor_a.pins[0].scenePos()
    pin1 = item.anchor_a.pins[1].scenePos()
    assert pin0.x() == pytest.approx(pin1.x()), "Pins should be vertical initially"
    # Rotate 90: horizontal
    item.anchor_a.rotate_90()
    pin0r = item.anchor_a.pins[0].scenePos()
    pin1r = item.anchor_a.pins[1].scenePos()
    assert pin0r.y() == pytest.approx(pin1r.y()), "Pins should be horizontal after rotate_90"
    assert pin0r.x() != pytest.approx(pin1r.x()), "Pins should have different X after rotate_90"
    # Rotate 180: vertical again (inverted)
    item.anchor_a.rotate_90()
    pin0rr = item.anchor_a.pins[0].scenePos()
    pin1rr = item.anchor_a.pins[1].scenePos()
    assert pin0rr.x() == pytest.approx(pin1rr.x()), "Pins should be vertical after second rotate_90"
