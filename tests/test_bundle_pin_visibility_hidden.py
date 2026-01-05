import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_bundle_side_pin_hidden(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a, b = bundle.source_node, bundle.target_node
    # Ensure we have a bundle side
    assert getattr(a, '_bundle_side', None) is not None
    # Shield pin on bundle side should be present but hidden
    shield_pin = next((p for p in a.pins.values() if p.model.id == 'S'), None)
    assert shield_pin is not None
    assert not shield_pin.isVisible()

    # H/L pins should be visible
    hl_pins = [p for p in a.pins.values() if p.model.id in ('H', 'L')]
    assert all(p.isVisible() for p in hl_pins)
