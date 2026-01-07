# Feature Spec: Infinite Canvas & Viewport

## 1. Overview
The **Canvas** is the primary interaction surface for Talus Trace. It serves as the bridge between the Core's mathematical truth (mm) and the user's visual perception (pixels). It must support an infinite workspace with high-performance rendering for industrial-scale harnesses.

### Core Traits
1.  **Coordinate Dual-Truth:** The canvas maintains a transformation matrix that maps Core Millimeters to Viewport Pixels based on `theme_tokens.json`.
2.  **Infinite Workspace:** Supports seamless panning and zooming across thousands of entities without performance degradation.
3.  **Visual Decoupling:** The canvas is a "Dumb Visualizer"; it renders what the API tells it to and captures user clicks to emit Commands.
4.  **Semantic Grid:** A 20px (standard) grid that provides visual feedback and snapping for all "Draft-First" routing.

## 2. Coordinate Math & Scaling

### 2.1. The Transformation Matrix
The Canvas uses the `physical_scale` from `theme_tokens.json` to calculate the zoom level.
* **Base Formula:** `1.0 Zoom` = `20 Pixels` per `1.0 Unit` (Default: Inch).
* **Millimeter Translation:** Since the Core stores data in **mm**, the UI calculates pixel position as:
    `Pixel_Pos = (Core_mm / 25.4) * Pixels_Per_Inch`.

### 2.2. Level of Detail (LOD)
To maintain 60FPS on complex harnesses, the Canvas implements LOD thresholds:
* **Standard View:** Full rendering of wire labels, pin identifiers, and helix patterns.
* **Performance View:** Triggered at `lod_threshold_scale` (Default: 0.5). Hides labels and simplifies Twisted Pairs to basic hatch lines to save draw calls.

## 3. Visual Anatomy

### 3.1. Background & Grid
* **Color:** Driven by `canvas.background_color` (Default: Grey 900).
* **Minor Grid:** 20px steps, low opacity.
* **Major Grid:** 100px steps, high contrast, used for visual anchoring.

### 3.2. Interaction Overlays
* **Selection Halo:** An orange glow around selected entities (Theme: `select_halo`).
* **Active Drag:** A red tint or ghosting effect during a move operation (Theme: `active_drag`).

## 4. Interaction Logic

### 4.1. Navigation
* **Middle-Mouse / Space+Click:** Pans the viewport.
* **Scroll Wheel:** Zooms centered on the mouse cursor position.

### 4.2. Command Emission
The Canvas does not modify the Core directly. It captures events and routes them to the **API Layer**:
1.  **Click & Drag:** Identifies the `target_id`.
2.  **Release:** Calculates the final `mm` delta.
3.  **Emit:** Sends a `MOVE_NODE` or `MOVE_DEVICE` command via the API.

## 5. Technical Implementation (UI Layer)

```python
class TalusCanvas(QGraphicsView):
    def __init__(self, api_link):
        super().__init__()
        self.api = api_link
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
    def drawBackground(self, painter, rect):
        # Implementation of 20px / 100px grid logic
        # Must respect theme_tokens.json layout values
        pass
        
    def mouseReleaseEvent(self, event):
        # Calculate target Core mm coordinates
        # api.execute(MoveCommand(target_id, new_mm_pos))
        pass
```