# Talus Trace Functional Specification

**Version:** 2.0 (Golden Copy)
**Scope:** Entity Behavior, Interaction Logic, and Fabrication Rules.

---

## PART 1: CORE ENTITIES

### 1. Twisted Pair (TwistedBundle)
* **Visuals:**
    * **High Detail (Zoom > LOD):** Render procedural Double-Helix.
    * **Low Detail (Zoom < LOD):** Render simple thick line with hatch pattern.
* **Behavior:**
    * **Control Node:** The sole pivot point. Dragging moves the node; Pins/Leaders track rigidly.
    * **Rotation:** `Space` rotates Pins 90° around the Node. Must snap to Grid.
* **Industrial Logic:** Length Calculation includes "Twist Factor" (e.g., +2-5% physical length).

### 2. Wire Bundle (Harness Trunk)
* **Visuals:**
    * **Calculated Diameter:** Width is derived from the **Packing Factor** of contained wires ($D \approx 1.15 \times \sqrt{\sum d^2}$), converted to pixels via `physical_scale`.
* **Behavior:**
    * **Entry Anchor:** When connecting to a Device, the Trunk Tip snaps to the **Device's Bundle Entry Anchor** (Connector Backshell), NOT the device origin.
    * **Atomic Connectivity:** Splitting a bundle must preserve internal logical nets.

### 3. Device (Entity)
* **Visuals (Dual Geometry):**
    * **Schematic Mode:** `AutoBox` (Logical Rect) snapped to Grid.
    * **Fabrication Mode:** `PhysicalSVG` (Real Outline) 1:1 scale.
    * **Visual Compensation:** In Fab Mode, draw "Pigtails" from Grid Pin to Physical Pin.
* **Behavior:**
    * **Cascading Deletion:** Deleting a Device automatically deletes all attached Wires/Labels (Transaction Safe).
    * **Service Loop:** Metadata property `add_length_mm` adds hidden length to connected wires for BOM calculations.

### 4. Wire (Entity)
* **Visuals:** Orthogonal Only. Width `3px`. Color inherits from Net.
* **Behavior:**
    * **Signal Propagation:** Changing a property (Color) updates the entire Net across Splices/Bundles.
    * **Orthogonal Constraint:** All segments MUST be Horizontal or Vertical.
* **BOM Logic:** Reported Length = (Geometric Length) + (Source Service Loop) + (Target Service Loop).

### 5. Pin (Entity)
* **Visuals:** Head on Grid. Tail bridges gap to Device Body (Variable Length).
* **Contrast:** Render 1px border if Pin Color matches Canvas Background.
* **Behavior:** Head Center MUST be on Grid (`x % 20 == 0`).

---

## PART 2: INTERACTION & SYSTEM

### 6. Interaction Logic
* **Command Pattern:** All user actions (Drag, Delete, Connect) MUST fire a `Command` object via the API. The View Layer (Qt) MUST NOT mutate the Model directly.
* **Placement Ghosting:**
    * Dragging new items shows a semi-transparent preview (`ghost_opacity`).
    * Ghost Snaps to Grid in real-time.
    * **Validation:** Red tint if placement is invalid; Blue tint if valid.

### 7. Fabrication (Nailboard)
* **Tiled Exporter:**
    * Converts the 1:1 Virtual Canvas into a physical template using standard consumer printers (Letter/A4).
    * **Registration Marks:** Renders crosshairs at page corners for alignment.
* **Fixture Entity:** Represents Clips, Tape, Grommets (Non-electrical BOM items).