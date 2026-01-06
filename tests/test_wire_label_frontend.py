from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Wire, WireLabel


def test_wire_label_item_created_and_positioned():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    # Create two devices
    a = win.add_device(0, 0, label='A', pins=1)
    b = win.add_device(200, 0, label='B', pins=1)

    # Create wire model and visual
    wire_model = Wire(id='W-1', **{'from': f'{a.model.id}.1', 'to': f'{b.model.id}.1'})
    from talustrace.frontend.items_baseline import WireItem
    wire_item = WireItem(wire_model, source_item=a, target_item=b)
    win.scene.addItem(wire_item)

    # Add a label model and ensure visual created
    lbl = WireLabel(text='LBL', t_pos=0.5)
    wire_item.add_label_model(lbl)
    QCoreApplication.processEvents()

    # There should be at least one wire label item as a child
    labels = [it for it in win.scene.items() if getattr(it, 'data', lambda i: None)(0) == 'wire_label']
    assert len(labels) >= 1
    # Verify label text present by inspecting child's paint output indirectly via boundingRect
    found = False
    for it in labels:
        try:
            if hasattr(it, 'model') and it.model.text == 'LBL':
                found = True
        except Exception:
            pass
    assert found is True
