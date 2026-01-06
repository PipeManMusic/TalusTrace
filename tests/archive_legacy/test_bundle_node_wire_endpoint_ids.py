import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_wires_to_nodes_get_persist_ids(qapp):
    win = MainWindow(restore_policy='skip')
    bundle = win.add_twisted_bundle(0, 0, spacing=120)
    a = bundle.source_node
    d = win.add_device(200, 0, label='D', pins=1, mark_dirty=False)

    # connect device pin to node's connectable pin
    connectable = [p for p in a.pins.values() if a.pin_connectable(p.model.id)][0]
    win.handle_wire_creation(d.pins['1'], connectable)

    # Wire model should have an endpoint like 'NODExxxx.H'
    assert len(win.wire_items) == 1
    w = win.wire_items[0]
    assert w.model.from_conn.count('.') == 1
    assert w.model.to_conn.startswith('NODE')
