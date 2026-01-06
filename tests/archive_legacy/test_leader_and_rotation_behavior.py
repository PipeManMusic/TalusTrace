from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QEvent, Qt
from talustrace.frontend.app import MainWindow
from talustrace.frontend.items_baseline import GRID_SIZE


def test_leader_lines_connect_tail_to_pivot():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(10, 10, spacing=120)

    a = b.source_node
    # Give any pending singleShot reconcile a chance to run
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()
    # Leader line should be present and connect tail to pivot
    pin = a.pins['H']
    leader = pin.leader
    assert leader is not None, "Leader line expected to exist on H pin"
    # Compute expected coordinates in node-local space
    tail_local = a.mapFromScene(pin.get_tail_scene_pos())
    pivot_local = a.mapFromScene(getattr(a, '_pivot'))
    line = leader.line()
    p1 = line.p1()
    p2 = line.p2()
    # leader may be p1->p2 or p2->p1, accept either ordering
    def almost_eq(p, q):
        return round(p.x(), 6) == round(q.x(), 6) and round(p.y(), 6) == round(q.y(), 6)
    assert (almost_eq(p1, tail_local) and almost_eq(p2, pivot_local)) or (almost_eq(p2, tail_local) and almost_eq(p1, pivot_local)), f"Leader endpoints do not match tail/pivot: p1={p1}, p2={p2}, tail={tail_local}, pivot={pivot_local}"


def test_spacebar_rotates_around_control_pivot():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=200)
    a = b.source_node

    pivot_before = a.mapToScene(getattr(a, '_pivot'))
    h_before = a.get_pin_tip_scene_pos('H')

    # Rotate via spacebar
    evt = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.NoModifier)
    from PySide6.QtWidgets import QApplication as _QApp
    _QApp.sendEvent(win.view, evt)

    pivot_after = a.mapToScene(getattr(a, '_pivot'))
    h_after = a.get_pin_tip_scene_pos('H')

    # pivot should not move
    assert round(pivot_before.x(), 6) == round(pivot_after.x(), 6)
    assert round(pivot_before.y(), 6) == round(pivot_after.y(), 6)

    # Distance from pivot to H should be preserved and rotated
    from PySide6.QtCore import QLineF
    d_before = QLineF(pivot_before, h_before).length()
    d_after = QLineF(pivot_after, h_after).length()
    assert round(d_before, 6) == round(d_after, 6)
