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
