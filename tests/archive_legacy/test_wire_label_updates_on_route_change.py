from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QPointF, QLineF
from talustrace.frontend.app import MainWindow
from talustrace.backend.models import Wire, WireLabel


def test_wire_label_tracks_route_changes():
    app = QApplication.instance() or QApplication([])
    win = MainWindow(restore_policy='skip')

    # Create two devices and a wire
    a = win.add_device(0, 0, label='A', pins=1)
    b = win.add_device(200, 0, label='B', pins=1)
    wire_model = Wire(id='W-2', **{'from': f'{a.model.id}.1', 'to': f'{b.model.id}.1'})
    from talustrace.frontend.items_baseline import WireItem
    wire_item = WireItem(wire_model, source_item=a, target_item=b)
    win.scene.addItem(wire_item)

    # Add label at middle
    lbl = WireLabel(text='MID', t_pos=0.5)
    wire_item.add_label_model(lbl)
    QCoreApplication.processEvents()

    labels = [it for it in win.scene.items() if getattr(it, 'data', lambda i: None)(0) == 'wire_label']
    assert labels
    lbl_item = next((it for it in labels if getattr(it, 'model', None) and it.model.text == 'MID'), None)
    assert lbl_item is not None

    # Snapshot initial projection and label world position
    nodes_before = wire_item._build_nodes()

    def compute_pt_at(nodes, t):
        seg_lengths = []
        total = 0.0
        for i in range(len(nodes) - 1):
            seg_len = QLineF(nodes[i], nodes[i + 1]).length()
            seg_lengths.append(seg_len)
            total += seg_len
        if total == 0:
            return nodes[0]
        target = t * total
        acc = 0.0
        for i, seg_len in enumerate(seg_lengths):
            if seg_len == 0:
                continue
            if acc + seg_len >= target:
                local_t = (target - acc) / seg_len
                a, b = nodes[i], nodes[i + 1]
                x = a.x() + (b.x() - a.x()) * local_t
                y = a.y() + (b.y() - a.y()) * local_t
                return QPointF(x, y)
            acc += seg_len
        return nodes[-1]

    pt_before = compute_pt_at(nodes_before, 0.5)
    # debug
    print(f"nodes_before={nodes_before}")
    print(f"pt_before={pt_before} label_pos_local={lbl_item.pos()} label_pos_world={lbl_item.mapToScene(lbl_item.boundingRect().center())}")
    before = lbl_item.mapToScene(lbl_item.boundingRect().center())

    # Add an elbow route point that should pull the wire downwards
    wire_item.model.route.append((100, 60))
    wire_item.update_geometry(rebuild_handles=True)
    QCoreApplication.processEvents()

    nodes_after = wire_item._build_nodes()
    pt_after = compute_pt_at(nodes_after, 0.5)
    after = lbl_item.mapToScene(lbl_item.boundingRect().center())

    # The computed projection along the path should move downwards
    assert pt_after.y() > pt_before.y(), f"expected projected point to move; before={pt_before} after={pt_after}"

    # Label visual should track that change (scene y should increase)
    assert after.y() > before.y(), f"Label world pos did not change; before={before} after={after}"
