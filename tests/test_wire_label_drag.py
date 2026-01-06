from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QPointF, Qt
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Wire, WireLabel


def test_wire_label_drag_updates_model():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    # Create two devices
    a = win.add_device(0, 0, label='A', pins=1)
    b = win.add_device(200, 0, label='B', pins=1)

    # Create wire and visual
    wire_model = Wire(id='W-1', **{'from': f'{a.model.id}.1', 'to': f'{b.model.id}.1'})
    from talustrace.frontend.items_baseline import WireItem
    wire_item = WireItem(wire_model, source_item=a, target_item=b)
    win.scene.addItem(wire_item)

    # Add a label near the start
    lbl = WireLabel(text='DRG', t_pos=0.2)
    wire_item.add_label_model(lbl)
    QCoreApplication.processEvents()

    # Locate the label item
    labels = [it for it in win.scene.items() if getattr(it, 'data', lambda i: None)(0) == 'wire_label']
    assert labels, "No wire label items found"
    lbl_item = None
    for it in labels:
        try:
            if getattr(it, 'model', None) and it.model.text == 'DRG':
                lbl_item = it
                break
        except Exception:
            pass
    assert lbl_item is not None

    # Press on the label and drag to near 75% along the wire
    start_scene = lbl_item.mapToScene(lbl_item.boundingRect().center())
    ev_press = QGraphicsSceneMouseEvent()
    ev_press.setScenePos(start_scene)
    ev_press.setButton(Qt.LeftButton)
    ev_press.setButtons(Qt.LeftButton)
    lbl_item.mousePressEvent(ev_press)

    # Move to a point near the second half of the wire
    ev_move = QGraphicsSceneMouseEvent()
    ev_move.setScenePos(QPointF(150, 10))
    ev_move.setButtons(Qt.LeftButton)
    lbl_item.mouseMoveEvent(ev_move)

    # The underlying model t_pos should have been updated to roughly 0.75
    assert lbl_item.model.t_pos > 0.6 and lbl_item.model.t_pos < 0.9

    # Release to finish drag
    ev_rel = QGraphicsSceneMouseEvent()
    ev_rel.setScenePos(QPointF(150, 10))
    ev_rel.setButton(Qt.LeftButton)
    ev_rel.setButtons(Qt.NoButton)
    lbl_item.mouseReleaseEvent(ev_rel)

    # Ensure final t_pos is still reasonable
    assert lbl_item.model.t_pos > 0.6 and lbl_item.model.t_pos < 0.95
