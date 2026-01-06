import pytest
from PySide6.QtWidgets import QGraphicsScene, QGraphicsPathItem
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

def test_helix_has_path(scene):
    item = make_item()
    scene.addItem(item)
    # Should be a QGraphicsPathItem or have a path() method
    helix = item.helix
    assert hasattr(helix, 'path'), "helix should have a path() method"
    path = helix.path()
    assert not path.isEmpty(), "helix.path() should not be empty (should have geometry)"

def test_helix_updates_on_anchor_move(scene):
    item = make_item()
    scene.addItem(item)
    helix = item.helix
    rect1 = helix.path().boundingRect()
    # Move anchor_b and update
    item.anchor_b.setPos(200, 50)
    item.update_layout()
    rect2 = helix.path().boundingRect()
    assert rect1 != rect2, f"Helix path bounding rect should change after anchor move. Before: {rect1}, After: {rect2}"

def test_helix_properties(scene):
    item = make_item()
    scene.addItem(item)
    helix = item.helix
    # Check for strand access (optional, will fail if not implemented)
    assert hasattr(helix, 'strands') or hasattr(helix, 'set_strand_colors'), "Helix should expose strand data or color setters for future visual tests."
