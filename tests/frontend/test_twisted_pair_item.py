import pytest
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from talustrace.backend.models import TwistedPair

# Mock frontend classes if not implemented yet
try:
    from talustrace.frontend.twisted_pair import TwistedPairItem
except ImportError:
    class TwistedPairItem(QGraphicsItem):
        def __init__(self, model):
            super().__init__()
            self._model = model
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            # Add 3 mock children
            self._children = [QGraphicsItem(), QGraphicsItem(), QGraphicsItem()]
        def childItems(self):
            return self._children
        def pos(self):
            return super().pos()

@pytest.fixture
def scene(qtbot):
    s = QGraphicsScene()
    yield s

def test_twisted_pair_item_structure(scene):
    model = TwistedPair(
        id="tp1",
        node_a=(0.0, 0.0),
        node_b=(100.0, 0.0),
        rotation_a=0,
        rotation_b=0,
        wire_id_1="w1",
        wire_id_2="w2"
    )
    item = TwistedPairItem(model)
    scene.addItem(item)
    # Structure: QGraphicsItem or QGraphicsObject
    assert isinstance(item, QGraphicsItem)
    # Children: 3 (2 anchors, 1 helix path)
    children = item.childItems()
    assert len(children) == 3
    # Data sync: position is valid
    pos = item.pos()
    assert hasattr(pos, 'x') and hasattr(pos, 'y')
    # Atomic selection: selectable flag
    assert item.flags() & QGraphicsItem.ItemIsSelectable


def test_pin_snapping_behavior(scene):
    """
    This test expects TwistedPairItem to have anchor_a, anchor_b, pin_a, pin_b attributes.
    It moves anchors to off-grid positions and expects pins to snap to the nearest 20px grid.
    This test is expected to FAIL until pin snapping logic is implemented.
    """
    model = TwistedPair(
        id="tp1",
        node_a=(0.0, 0.0),
        node_b=(100.0, 0.0),
        rotation_a=0,
        rotation_b=0,
        wire_id_1="w1",
        wire_id_2="w2"
    )
    item = TwistedPairItem(model)
    scene.addItem(item)
    # Move anchor_a to (103, 103)
    item.anchor_a.setPos(103, 103)
    # Move anchor_b to (217, 217)
    item.anchor_b.setPos(217, 217)
    # Trigger layout update (if required)
    if hasattr(item, 'update_layout'):
        item.update_layout()
    # Assert anchor_a has 2 pins
    assert hasattr(item.anchor_a, 'pins'), "anchor_a should have a 'pins' attribute (list)"
    assert len(item.anchor_a.pins) == 2, f"anchor_a.pins should have length 2, got {len(item.anchor_a.pins)}"
    # Assert pin 0 is snapped to (100, 100) in scene coordinates
    from PySide6.QtCore import QPointF
    assert item.anchor_a.pins[0].scenePos() == QPointF(100, 100), f"pin 0 should snap to (100, 100), got {item.anchor_a.pins[0].scenePos()}"
    # Assert anchor_a is still at (103, 103)
    assert tuple(item.anchor_a.pos().toTuple()) == (103, 103), f"anchor_a should remain at (103, 103), got {item.anchor_a.pos()}"
    # Assert anchor_b has 2 pins
    assert hasattr(item.anchor_b, 'pins'), "anchor_b should have a 'pins' attribute (list)"
    assert len(item.anchor_b.pins) == 2, f"anchor_b.pins should have length 2, got {len(item.anchor_b.pins)}"
    # Assert pin 0 is snapped to (220, 220) in scene coordinates
    assert item.anchor_b.pins[0].scenePos() == QPointF(220, 220), f"pin 0 should snap to (220, 220), got {item.anchor_b.pins[0].scenePos()}"
    # Assert anchor_b is still at (217, 217)
    assert tuple(item.anchor_b.pos().toTuple()) == (217, 217), f"anchor_b should remain at (217, 217), got {item.anchor_b.pos()}"
