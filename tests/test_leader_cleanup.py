from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QGraphicsLineItem
from talustrace.frontend.app import MainWindow


def leaders_for_node(node):
    # Return set of QGraphicsLineItem instances parented directly to node
    return {it for it in node.scene().items() if isinstance(it, QGraphicsLineItem) and it.parentItem() is node}


def test_rebuild_pins_does_not_leave_stale_leaders():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a, c = b.source_node, b.target_node

    # initial leaders
    for _ in range(3):
        a._build_pins()
    leaders = leaders_for_node(a)
    # leaders should exactly match pin.leader for each pin
    expected = {pin.leader for pin in a.pins.values() if getattr(pin, 'leader', None) is not None}
    assert leaders == expected


def test_delete_pin_removes_leader():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    d = win.add_device(0, 0, pins=3, mark_dirty=False)
    # pick a pin to delete
    pin_item = list(d.pins.values())[0]
    leader_ref = getattr(pin_item, 'leader', None)
    win._delete_pin_item(d, pin_item)
    # after delete, leader should be removed from scene
    if leader_ref:
        assert leader_ref.scene() is None
