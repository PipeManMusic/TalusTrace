import subprocess
from PySide6.QtGui import QImage
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QApplication
from talustrace.frontend.device_minimal import DeviceItem
from talustrace.frontend.items_baseline import TwistNodeItem, GRID_SIZE
from talustrace.frontend.twisted_bundle import TwistedBundleItem


def run_renderer():
    cmd = ["python3", "scripts/demo_render.py", "--mode", "device", "--padding", "10", "--diagnose"]
    env = {**__import__('os').environ, 'QT_QPA_PLATFORM': 'offscreen'}
    completed = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert completed.returncode == 0, f"Renderer failed: stdout={completed.stdout}\nstderr={completed.stderr}"


def test_diag_overlay_only_pivots():
    # Ensure QApplication exists
    app = QApplication.instance() or QApplication([])
    # Run renderer to produce diagnostic image
    run_renderer()
    path = 'artifacts/demo_state_pad10_diag.png'

    img = QImage(path)
    assert not img.isNull(), 'Diagnostic image failed to load'
    w, h = img.width(), img.height()

    # Reconstruct the scene geometry used by the renderer to compute the render rect
    scene_devices = [DeviceItem(60, 60), DeviceItem(260, 60)]
    n1 = TwistNodeItem(on_changed=None)
    n2 = TwistNodeItem(on_changed=None)
    n1.setPos(60, 160)
    n2.setPos(260, 160)
    bundle = TwistedBundleItem(n1, n2, on_changed=None)

    # Compute candidate rects as demo_render does
    candidate_rects = []
    for d in scene_devices:
        candidate_rects.append(d.mapToScene(d.boundingRect()).boundingRect())
    try:
        pts = bundle._poly_points()
        if pts:
            minx = min(p.x() for p in pts)
            maxx = max(p.x() for p in pts)
            miny = min(p.y() for p in pts)
            maxy = max(p.y() for p in pts)
            candidate_rects.append(QRectF(minx, miny, maxx - minx, maxy - miny))
    except Exception:
        pass
    rect = candidate_rects[0]
    for r in candidate_rects[1:]:
        rect = rect.united(r)
    # Expand vertically to include pin extents
    pin_extents = []
    for n in (n1, n2):
        for pin in n.pins.values():
            rr = pin.mapToScene(pin.boundingRect()).boundingRect()
            pin_extents.append((rr.top(), rr.bottom()))
    if pin_extents:
        min_pin_top = min(t for (t, b) in pin_extents)
        max_pin_bottom = max(b for (t, b) in pin_extents)
        if min_pin_top < rect.top():
            rect.setTop(min_pin_top)
        if max_pin_bottom > rect.bottom():
            rect.setBottom(max_pin_bottom)
    pad = 10
    rect = rect.adjusted(-pad, -pad, pad, pad)

    # Compute pivot bounding rects in image coordinates
    pivot_rects = []
    for node in (n1, n2):
        cp = getattr(node, 'control_pivot', None)
        assert cp is not None
        br = cp.mapToScene(cp.boundingRect()).boundingRect()
        # Convert to image pixel coords
        x = int(br.left() - rect.left())
        y = int(br.top() - rect.top())
        wbr = int(br.width())
        hbr = int(br.height())
        # Allow small expansion
        pad_px = 3
        pivot_rects.append((x - pad_px, y - pad_px, wbr + pad_px * 2, hbr + pad_px * 2))

    # Inspect non-background pixels in the diagnostic image and ensure they lie within pivot rects
    non_bg = 0
    out_of_bounds = []
    for yy in range(h):
        for xx in range(w):
            c = img.pixelColor(xx, yy)
            # Treat white and grid gray as background
            if (c.red() == 255 and c.green() == 255 and c.blue() == 255) or (c.red() == 230 and c.green() == 230 and c.blue() == 230):
                continue
            non_bg += 1
            ok = False
            for (rx, ry, rw, rh) in pivot_rects:
                if xx >= rx and xx < rx + rw and yy >= ry and yy < ry + rh:
                    ok = True
                    break
            if not ok:
                # If the color is orange-like (diagnostic overlay color), flag it as out-of-bounds.
                # Allow other scene colors (bundle wires etc.) outside pivots.
                dr = c.red() - 255
                dg = c.green() - 140
                db = c.blue() - 0
                dist = (dr*dr + dg*dg + db*db) ** 0.5
                if dist < 80:
                    out_of_bounds.append((xx, yy, c.red(), c.green(), c.blue()))
    assert non_bg > 0, 'No diagnostic overlay pixels found'
    assert not out_of_bounds, f'Found diagnostic overlay (orange) pixels outside control pivots: {out_of_bounds[:10]}'
