from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Side


def _assert_close(a: QPointF, b: QPointF, tol: float = 4.0):
    dx = a.x() - b.x()
    dy = a.y() - b.y()
    dist = (dx*dx + dy*dy) ** 0.5
    assert dist <= tol, f"Points not close: {a} vs {b} (dist={dist})"


def test_wire_attached_to_twistnode_moves_with_node():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    # Create twist nodes via bundle helper
    b = win.add_twisted_bundle(200, 0)
    n = b.source_node

    # Create a device and connect it to the twist node
    d = win.add_device(0, 0, mark_dirty=False)
    d.add_pin_model(side=Side.RIGHT, label='p1', pin_id='1')
    win.handle_wire_creation(d.pins['1'], n.pins['H'])
    w = win.wire_items[-1]

    # Add an elbow on the wire and verify initial alignment
    w.add_elbow_at(QPointF(80, 0))
    assert len(w.model.route) == 1
    route_pt = QPointF(*w.model.route[0])
    handle_scene = w.elbow_handles[0].mapToScene(w.elbow_handles[0].boundingRect().center())
    _assert_close(handle_scene, route_pt)

    # Move the twist node and ensure the attached wire updates
    new_pos = n.pos() + QPointF(20, 20)
    n.setPos(new_pos)

    # After moving the node, wire should update and elbow handle should still match route point
    route_pt = QPointF(*w.model.route[0])
    handle_scene = w.elbow_handles[0].mapToScene(w.elbow_handles[0].boundingRect().center())
    _assert_close(handle_scene, route_pt)
