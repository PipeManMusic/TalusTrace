import pytest
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QColor
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

def test_signal_updates_helix_color(scene):
    item = make_item()
    scene.addItem(item)
    # Step 1: Set signal on anchor_a pin 0 (should update helix color1)
    item.set_signal(item.anchor_a.pins[0], wire_id="WIRE_A", color="#00FF00")
    assert item.helix.color1 == QColor("#00FF00"), f"Helix color1 should be #00FF00, got {item.helix.color1.name()}"
    # Step 2: Set signal on anchor_a pin 1 (should update helix color2)
    item.set_signal(item.anchor_a.pins[1], wire_id="WIRE_B", color="#FF00FF")
    assert item.helix.color2 == QColor("#FF00FF"), f"Helix color2 should be #FF00FF, got {item.helix.color2.name()}"
    # Step 3: Set signal on anchor_b pin 0 (should also update helix color1)
    item.set_signal(item.anchor_b.pins[0], wire_id="WIRE_A2", color="#0000FF")
    assert item.helix.color1 == QColor("#0000FF"), f"Helix color1 should be #0000FF after setting anchor_b.pins[0], got {item.helix.color1.name()}"
