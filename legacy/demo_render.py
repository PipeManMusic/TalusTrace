#!/usr/bin/env python3
"""Render a snapshot of the current scene (DeviceItems + TwistedBundle) to a PNG.
This runs with QT_QPA_PLATFORM=offscreen so it works in CI/headless environments.
"""
import os
import sys

# Ensure project root is on path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from PySide6.QtWidgets import QApplication, QGraphicsScene
import math
from PySide6.QtGui import QPainter, QImage, QPen, QColor
from PySide6.QtCore import QRectF, Qt

from talustrace.frontend.device_minimal import DeviceItem
from talustrace.frontend.items_baseline import TwistNodeItem
from talustrace.frontend.twisted_bundle import TwistedBundleItem

OUT = os.path.join(root, 'artifacts')
os.makedirs(OUT, exist_ok=True)

# CLI: choose crop mode and padding
import argparse
parser = argparse.ArgumentParser(description='Render a snapshot of the scene (devices + bundle)')
parser.add_argument('--mode', choices=('device','core','context'), default='device', help='Crop mode: "device" uses device bounds+bundle poly; "core" uses tightened bundle/pin envelopes; "context" uses full scene bounds')
parser.add_argument('--padding', type=int, default=10, help='Padding in pixels to add around computed rect')
parser.add_argument('--bundle-envelope', type=int, default=10, help='Vertical envelope (px) around bundle centerline for core mode')
parser.add_argument('--pin-clamp', type=int, default=24, help='Maximum vertical expansion (px) allowed for pin extents around device bounds in core mode')
parser.add_argument('--diagnose', action='store_true', help='If set, highlight and report hidden/stray items in the snapshot (diagnostic overlay)')
args = parser.parse_args()

OUT_FILE = os.path.join(OUT, f"demo_state_pad{args.padding}.png")

# Create offscreen app
app = QApplication.instance() or QApplication([])

scene = QGraphicsScene()
from PySide6.QtGui import QColor
scene.setBackgroundBrush(QColor('#ffffff'))

# Add two minimal devices
d1 = DeviceItem(60, 60)
scene.addItem(d1)

d2 = DeviceItem(260, 60)
scene.addItem(d2)

# Add two twist nodes and a bundle (to show bundle visuals)
n1 = TwistNodeItem(on_changed=None)
n2 = TwistNodeItem(on_changed=None)
n1.setPos(60, 160)
n2.setPos(260, 160)
scene.addItem(n1)
scene.addItem(n2)

bundle = TwistedBundleItem(n1, n2, on_changed=None)
scene.addItem(bundle)

# Force layout updates
for item in (n1, n2, bundle, d1, d2):
    try:
        if hasattr(item, '_enforce_pin_grid'):
            item._enforce_pin_grid()
        if hasattr(item, '_update_pivot_from_pins'):
            item._update_pivot_from_pins()
    except Exception:
        pass

# Inspect all ellipse items to diagnose visual artifacts
from PySide6.QtWidgets import QGraphicsEllipseItem
ellipses = [it for it in scene.items() if isinstance(it, QGraphicsEllipseItem)]
print(f"Found {len(ellipses)} ellipse item(s) in scene")
for idx, it in enumerate(ellipses, 1):
    parent = it.parentItem()
    parent_name = parent.__class__.__name__ if parent else 'None'
    pos = it.mapToScene(it.boundingRect().center())
    pen = it.pen() if hasattr(it, 'pen') else None
    brush = it.brush() if hasattr(it, 'brush') else None
    z = it.zValue()
    try:
        data0 = it.data(0)
    except Exception:
        data0 = None
    # Show brush style name and detect NoBrush robustly
    if brush is None:
        brush_str = 'none'
    else:
        try:
            brush_style = brush.style()
            brush_str = str(brush_style)
        except Exception:
            brush_str = 'unknown'
    is_none = brush is None or (isinstance(brush_str, str) and 'NoBrush' in brush_str)
    print(f"Ellipse #{idx}: parent={parent_name}, pos=({pos.x():.1f},{pos.y():.1f}), pen={pen.color().name() if pen and hasattr(pen,'color') else pen}, brush={'none' if is_none else brush_str}, z={z}, data0={data0}")

# Remove any stray top-level ellipse items (visual-only cleanup for demo snapshot)
removed = 0
for it in list(scene.items()):
    try:
        if isinstance(it, QGraphicsEllipseItem) and it.parentItem() is None:
            scene.removeItem(it)
            removed += 1
    except Exception:
        pass
if removed:
    print(f"Removed {removed} stray ellipse item(s) from scene for demo rendering")

# Detect any stray top-level line items (not attached to nodes) so they can be
# included in the diagnostic set. Do not mutate scene items unless --diagnose is set.
from PySide6.QtWidgets import QGraphicsLineItem
stray_line_rects = []
for it in list(scene.items()):
    try:
        if isinstance(it, QGraphicsLineItem) and it.parentItem() is None:
            try:
                r = it.mapToScene(it.boundingRect()).boundingRect()
                stray_line_rects.append((it, r))
            except Exception:
                stray_line_rects.append((it, None))
    except Exception:
        pass
if stray_line_rects:
    print(f"Detected {len(stray_line_rects)} stray top-level line(s) (diagnose mode will overlay)")

# Find any items that are hidden (not visible). If diagnose mode is enabled
# we'll overlay their bounding boxes onto the rendered image for review. We will
# not change their visibility or mutate their pens/brushes here.
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsRectItem
hidden_items = []
for it in list(scene.items()):
    try:
        if not it.isVisible():
            # Avoid reporting core items
            if it.__class__.__name__ in ('DeviceItem', 'TwistNodeItem'):
                continue
            try:
                hidden_items.append((it, it.mapToScene(it.boundingRect()).boundingRect()))
            except Exception:
                hidden_items.append((it, None))
    except Exception:
        pass
if hidden_items:
    print(f"Detected {len(hidden_items)} hidden scene item(s) (diagnose mode will overlay)")

# Compute scene extents and render
# Prefer a tighter rect computed from DeviceItem bounds and TwistedBundle poly points
from PySide6.QtCore import QRectF
candidate_rects = []
for it in scene.items():
    cls = it.__class__.__name__
    try:
        if cls == 'DeviceItem':
            candidate_rects.append(it.mapToScene(it.boundingRect()).boundingRect())
        elif cls == 'TwistedBundleItem':
            # Use the bundle poly points (actual geometry) rather than the stroked envelope
            try:
                pts = it._poly_points()
                if pts:
                    minx = min(p.x() for p in pts)
                    maxx = max(p.x() for p in pts)
                    miny = min(p.y() for p in pts)
                    maxy = max(p.y() for p in pts)
                    candidate_rects.append(QRectF(minx, miny, maxx - minx, maxy - miny))
            except Exception:
                pass
    except Exception:
        pass
# If recolored stray lines were recorded, include their rects so they appear in the crop
try:
    if stray_line_rects:
        for r in stray_line_rects:
            candidate_rects.append(r)
        print(f"Included {len(stray_line_rects)} stray top-level line rect(s) into candidate rects for rendering")
except Exception:
    pass

# Also collect vertical extents from PinItem tips so we don't accidentally clip pin visuals.
pin_extents = []
for it in scene.items():
    try:
        if it.__class__.__name__ == 'PinItem':
            r = it.mapToScene(it.boundingRect()).boundingRect()
            pin_extents.append((r.top(), r.bottom()))
    except Exception:
        pass

if args.mode in ('device', 'core') and candidate_rects:
    # Base rect is union of device boxes & bundle polylines (centerline points)
    rect = candidate_rects[0]
    for r in candidate_rects[1:]:
        rect = rect.united(r)

    if args.mode == 'device':
        # Expand vertically to include any pin tops/bottoms without expanding horizontally
        if pin_extents:
            min_pin_top = min(t for (t, b) in pin_extents)
            max_pin_bottom = max(b for (t, b) in pin_extents)
            if min_pin_top < rect.top():
                rect.setTop(min_pin_top)
            if max_pin_bottom > rect.bottom():
                rect.setBottom(max_pin_bottom)
    else:
        # Core mode: tighten bundle vertical envelope and clamp pin extents to avoid including long stroked envelopes/handles
        bundle_env = args.bundle_envelope
        # Compute bundle centerline Y across available TwistedBundleItems
        bundle_ys = []
        for it in scene.items():
            try:
                if it.__class__.__name__ == 'TwistedBundleItem':
                    pts = it._poly_points()
                    for p in pts:
                        bundle_ys.append(p.y())
            except Exception:
                pass
        if bundle_ys:
            center_y = sum(bundle_ys) / len(bundle_ys)
            rect.setTop(min(rect.top(), center_y - bundle_env))
            rect.setBottom(max(rect.bottom(), center_y + bundle_env))
        # Clamp pin extents so they don't extend arbitrarily far from the device body
        if pin_extents:
            min_pin_top = min(t for (t, b) in pin_extents)
            max_pin_bottom = max(b for (t, b) in pin_extents)
            pin_clamp = args.pin_clamp
            min_allowed = rect.top() - pin_clamp
            max_allowed = rect.bottom() + pin_clamp
            clamped_top = max(min_pin_top, min_allowed)
            clamped_bottom = min(max_pin_bottom, max_allowed)
            if clamped_top < rect.top():
                rect.setTop(clamped_top)
            if clamped_bottom > rect.bottom():
                rect.setBottom(clamped_bottom)

    # Pad slightly to leave breathing room using requested padding
    pad = args.padding
    rect = rect.adjusted(-pad, -pad, pad, pad)
else:
    # Use full scene bounds when in context mode or no candidate rects
    pad = args.padding
    rect = scene.itemsBoundingRect()
    rect = rect.adjusted(-pad, -pad, pad, pad)

print(f"Mode={args.mode}, padding={args.padding}; render rect: left={rect.left():.1f}, top={rect.top():.1f}, right={rect.right():.1f}, bottom={rect.bottom():.1f}, w={rect.width():.1f}, h={rect.height():.1f}")
# For debugging: if any bundle geometry intersects the left edge of the render rect,
# recolor that bundle to orange so it is easy to spot in the generated image.
bundles_to_overlay = []
try:
    for it in scene.items():
        try:
            if it.__class__.__name__ == 'TwistedBundleItem':
                br = it.sceneBoundingRect()
                # If the bundle centerline points get close to the left edge of the render
                # rect (within 20px), highlight the bundle so we can identify its geometry.
                try:
                    pts = it._poly_points()
                    if pts:
                        minx = min(p.x() for p in pts)
                        if minx <= rect.left() + 20:
                            # Record bundles near left edge for diagnostic overlay (do not mutate scene)
                            try:
                                bundles_to_overlay.append((it, br))
                            except Exception:
                                bundles_to_overlay.append((it, None))
                            print(f"Bundle near left edge detected (diagnose mode will overlay): minx={minx}, bbox={br}")
                except Exception:
                    pass
        except Exception:
            pass
except Exception:
    pass
img = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
# Fill white background first
img.fill(0xffffffff)

# Draw a subtle grid (using the project's GRID_SIZE) onto the image before rendering the scene
try:
    from talustrace.frontend.items_baseline import GRID_SIZE
except Exception:
    GRID_SIZE = 20

p = QPainter(img)
old_bg = None
try:
    # Save original brush and disable scene background so it doesn't overwrite the grid
    try:
        old_bg = scene.backgroundBrush()
        scene.setBackgroundBrush(Qt.NoBrush)
    except Exception:
        old_bg = None

    # Light grid color
    grid_pen = QPen(QColor(230, 230, 230), 1)
    grid_pen.setStyle(Qt.SolidLine)
    p.setPen(grid_pen)
    # Draw crisp, non-antialiased lines for deterministic rasterization
    try:
        p.setRenderHint(QPainter.Antialiasing, False)
    except Exception:
        pass
    # Compute first grid lines in scene coords, then draw them mapped into image pixel coords
    left = rect.left()
    top = rect.top()
    right = rect.right()
    bottom = rect.bottom()
    # Vertical lines
    first_x = math.ceil(left / GRID_SIZE) * GRID_SIZE
    x = first_x
    while x <= right:
        px = x - left
        p.drawLine(int(px), 0, int(px), int(rect.height()))
        x += GRID_SIZE
    # Horizontal lines
    first_y = math.ceil(top / GRID_SIZE) * GRID_SIZE
    y = first_y
    while y <= bottom:
        py = y - top
        p.drawLine(0, int(py), int(rect.width()), int(py))
        y += GRID_SIZE

    # Render the scene on top of the grid
    scene.render(p, QRectF(img.rect()), rect)
finally:
    # Restore scene background
    try:
        if old_bg is not None:
            scene.setBackgroundBrush(old_bg)
    except Exception:
        pass
    # Ensure painter is ended to avoid paint device issues
    try:
        if p.isActive():
            p.end()
    except Exception:
        pass

# Diagnostic overlays: if requested, draw only ellipse halos over the bundle control pivots.
if args.diagnose:
    try:
        from PySide6.QtGui import QPainter, QPen, QBrush
        diag_out = OUT_FILE.replace('.png', '_diag.png')
        p2 = QPainter(img)
        try:
            p2.setPen(QPen(QColor(255, 140, 0), 2))
            p2.setBrush(QBrush(QColor(255, 140, 0, 64)))
            # Only highlight the control pivot ellipses for nodes that are part of a bundle
            nodes = set()
            for it in scene.items():
                try:
                    if it.__class__.__name__ == 'TwistedBundleItem':
                        nodes.add(it.source_node)
                        nodes.add(it.target_node)
                except Exception:
                    pass
            for node in nodes:
                try:
                    cp = getattr(node, 'control_pivot', None)
                    if not cp:
                        continue
                    br = cp.mapToScene(cp.boundingRect()).boundingRect()
                    x = br.left() - rect.left()
                    y = br.top() - rect.top()
                    w = br.width()
                    h = br.height()
                    p2.drawEllipse(int(x), int(y), int(w), int(h))
                except Exception:
                    pass
        finally:
            # Ensure painter is always ended before img goes out of scope
            try:
                if p2.isActive():
                    p2.end()
            except Exception:
                pass
        # Save diagnostic overlay image so the user can inspect highlights
        try:
            saved_diag = img.save(diag_out)
            if saved_diag:
                print('Saved diagnostic overlay to', diag_out)
            else:
                print('Failed to save diagnostic overlay to', diag_out)
        except Exception:
            pass
    except Exception:
        pass

saved = img.save(OUT_FILE)
if saved:
    print('Saved snapshot to', OUT_FILE)
else:
    print('Failed to save snapshot to', OUT_FILE)

# Two-pass cleanup: inspect the saved image for non-background pixels in the left region
# and remove scene items under those pixels (if they are not core items like devices/nodes).
# This removal is kept, but we avoid recoloring or revealing non-problem items.
try:
    from PySide6.QtGui import QImage
    clean_out = OUT_FILE.replace('.png', f'_clean.png')
    qi = QImage(OUT_FILE)
    w = qi.width()
    h = qi.height()
    # Scan leftmost columns to find the first column that contains non-background pixels
    first_non_bg_x = None
    for x in range(min(40, w)):
        found = False
        for y in range(h):
            c = qi.pixelColor(x, y)
            if (c.red() == 255 and c.green() == 255 and c.blue() == 255) or (c.red() == 230 and c.green() == 230 and c.blue() == 230):
                continue
            found = True
            break
        if found:
            first_non_bg_x = x
            break
    if first_non_bg_x is not None:
        # Map a small vertical strip in the image to scene coords and hit-test scene items
        scene_x = rect.left() + first_non_bg_x + 0.5
        margin = 6.0
        candidates = set()
        for it in scene.items():
            try:
                br = it.sceneBoundingRect()
                # intersect with narrow strip
                strip = QRectF(scene_x - margin, rect.top(), margin * 2, rect.height())
                if br.intersects(strip):
                    candidates.add(it)
            except Exception:
                pass
        # Filter removable candidate items conservatively: allow QGraphicsLineItem/QGraphicsPathItem/ElbowHandle/SegmentHandle or TwistedBundleItem
        removed_items = []
        from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
        for it in list(candidates):
            try:
                cls_name = it.__class__.__name__
                # Skip core items
                if cls_name in ('DeviceItem', 'TwistNodeItem'):
                    continue
                # Allow removal for these classes
                if isinstance(it, (QGraphicsLineItem, QGraphicsPathItem)) or cls_name in ('ElbowHandle', 'SegmentHandle', 'TwistedBundleItem'):
                    if it.scene():
                        it.scene().removeItem(it)
                        removed_items.append((cls_name, it.sceneBoundingRect()))
            except Exception:
                pass
        if removed_items:
            print(f"Removed {len(removed_items)} candidate scene item(s) intersecting left-edge problem area:")
            for cname, bbox in removed_items:
                print(f" - {cname} bbox={bbox}")
            # Re-render cleaned image
            img2 = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
            img2.fill(0xffffffff)
            p3 = QPainter(img2)
            try:
                # Redraw grid
                grid_pen = QPen(QColor(230, 230, 230), 1)
                p3.setPen(grid_pen)
                try:
                    p3.setRenderHint(QPainter.Antialiasing, False)
                except Exception:
                    pass
                # Vertical lines
                left = rect.left(); right = rect.right(); top = rect.top(); bottom = rect.bottom()
                first_x = math.ceil(left / GRID_SIZE) * GRID_SIZE
                x = first_x
                while x <= right:
                    px = x - left
                    p3.drawLine(int(px), 0, int(px), int(rect.height()))
                    x += GRID_SIZE
                # Horizontal lines
                first_y = math.ceil(top / GRID_SIZE) * GRID_SIZE
                y = first_y
                while y <= bottom:
                    py = y - top
                    p3.drawLine(0, int(py), int(rect.width()), int(py))
                    y += GRID_SIZE
                # Render the cleaned scene
                scene.render(p3, QRectF(img2.rect()), rect)
            finally:
                try:
                    if p3.isActive():
                        p3.end()
                except Exception:
                    pass
            saved2 = img2.save(clean_out)
            if saved2:
                print('Saved cleaned snapshot to', clean_out)
            else:
                print('Failed to save cleaned snapshot to', clean_out)
    else:
        print('No left-edge non-background pixels detected; no scene items removed.')
except Exception as e:
    print('Error during cleanup pass:', e)
