from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow


def test_pin_and_leader_use_bundle_colors():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=120)

    a = b.source_node
    # Give any pending reconcile a chance to run
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    # Bundle colors
    ca = b.color_a
    cb = b.color_b

    # H pin should match color_a
    h_pin = a.pins['H']
    assert h_pin.line.pen().color() == ca
    assert h_pin.leader is not None
    assert h_pin.leader.pen().color() == ca

    # L pin should match color_b
    l_pin = a.pins['L']
    assert l_pin.line.pen().color() == cb
    assert l_pin.leader is not None
    assert l_pin.leader.pen().color() == cb

    # Shield pin color should be a blend (midpoint) of ca and cb
    s_pin = a.pins['S']
    # Compute expected blend
    expected_r = (ca.red() + cb.red()) // 2
    expected_g = (ca.green() + cb.green()) // 2
    expected_b = (ca.blue() + cb.blue()) // 2
    expected = (expected_r, expected_g, expected_b)
    got = (s_pin.line.pen().color().red(), s_pin.line.pen().color().green(), s_pin.line.pen().color().blue())
    assert got == expected

    # Leader line thickness should match the pin line thickness (visual parity with wires)
    assert h_pin.leader.pen().widthF() == h_pin.line.pen().widthF()
    assert l_pin.leader.pen().widthF() == l_pin.line.pen().widthF()
    assert s_pin.leader.pen().widthF() == s_pin.line.pen().widthF()


def test_pin_hover_restores_color():
    """Hovering a pin should show the hover color, and leaving should restore the prior pin/bundle color."""
    from PySide6.QtWidgets import QGraphicsSceneHoverEvent
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')
    b = win.add_twisted_bundle(0, 0, spacing=120)
    a = b.source_node
    from PySide6.QtCore import QCoreApplication
    QCoreApplication.processEvents()

    from talustrace.frontend.items_baseline import PIN_HOVER_COLOR

    ca = b.color_a
    h_pin = a.pins['H']

    # Sanity check initial color
    assert h_pin.line.pen().color() == ca

    # Simulate hover enter
    ev = QGraphicsSceneHoverEvent()
    h_pin.hoverEnterEvent(ev)
    assert h_pin.line.pen().color() == PIN_HOVER_COLOR

    # Simulate hover leave; color should be restored to bundle color
    ev2 = QGraphicsSceneHoverEvent()
    h_pin.hoverLeaveEvent(ev2)
    assert h_pin.line.pen().color() == ca
    assert h_pin.leader.pen().color() == ca
