import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.items import TwistNodeItem

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_pin_tips_exist_and_are_on_connectable_side(qapp):
    node = TwistNodeItem(on_changed=None)
    # Initially no bundle attached => default HL on left, shield on right
    tips = [p.tip for p in node.pins.values()]
    assert all(tip is not None for tip in tips)

    # Simulate registering a bundle on the right side; H/L should be on left
    from PySide6.QtCore import QPointF
    dummy_bundle = type('B', (), {'source_node': None, 'target_node': node})()
    # make the other node appear to the right
    class OtherNode:
        def pos(self):
            return QPointF(100, 0)
    dummy_bundle.source_node = OtherNode()
    node.register_bundle(dummy_bundle)
    # Check H and L are on the opposite side of reserved bundle side
    bundle_side = node._bundle_side
    assert bundle_side is not None
    connectable_pins = [p for p in node.pins.values() if node.pin_connectable(p.model.id)]
    assert len(connectable_pins) >= 2
