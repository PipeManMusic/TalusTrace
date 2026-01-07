# Talus Trace Functional Specification
**Version:** 2.0

## 1. Inferred Topology (The Bundling Engine)
Grouping is determined by spatial overlap on the 20px grid.

### 1.1. Grid-Line Coalescence
* **Logic:** If multiple `Wire` segments share start and end coordinates, they merge into a **Bundle Segment**.
* **Visualization:** Overlapping wires collapse into a single thicker line in Diagram View.
* **Auto-Recalculation:** Moving a segment grip triggers a re-scan of coordinates to "split" or "merge" bundles.

### 1.2. Bundle Sizing
* **Algorithm:** Thickness ($D$) is calculated using the industrial packing factor: $D \approx 1.15 \times \sqrt{\sum d^2}$.
* **Asynchrony:** Recalculations run on background threads via Calculation Transactions.

## 2. Twisted Pair Atomic Logic
Twisted Pairs are treated as a single "Super-Wire" entity.

### 2.1. Synchronized Identity
* **Signal Propagation:** Connecting a signal to one end automatically assigns it to the other end.
* **Property Mirroring:** Changes to gauge or standard are instantly reflected at both ends.

### 2.2. Procedural Helix Rendering
* **Geometry:** Double-helix paths generated along the normal of a Cubic Bezier path.
* **LOD (Level of Detail):** High Detail (Double-Helix) vs. Low Detail (Simplified hatch).

## 3. Signal Tunneling
The Core tracks signals through "transparent" components (Twisted Pairs/Bundles). Active devices terminate signals unless a bridge map is defined.

## 4. Coordinate & Unit Translation
* **The Holy Millimeter:** Internal state is stored in `float` (mm).
* **Display Units:** The UI applies a transformation matrix based on the `physical_scale` token.
* **Calibration:** The Device Wizard calculates a `scale_factor` to ensure SVG graphics maintain 1:1 truth.

## 5. The Audit Pipeline
* **Monitoring:** The Constraint Engine runs in background threads.
* **Memoization:** Calculation results are written to the Calculation Cache YAML to prevent lag.