# Feature Spec: Custom Device Library & SVG Support

## 1. Overview
This feature introduces a comprehensive **Component Library System** to Talus Trace. It allows users to create, save, and reuse complex device definitions, including those with custom SVG graphics (e.g., connector footprints).

### Core Goals
1.  **Bi-Directional Workflow:** Create parts on the fly ("Save to Library") or design them deliberately ("Device Wizard").
2.  **Physical Fidelity:** Support custom SVG backgrounds for 1:1 formboard printing.
3.  **Grid Compliance:** Enforce strict grid snapping for connection points ("Heads") while allowing arbitrary placement for device contact points ("Tails").
4.  **Local-First:** All library parts are stored as self-contained YAML files.

---

## 2. User Workflows

### 2.1. The "Bottom-Up" Workflow (Promote to Library)
*User creates a generic box on the canvas, configures it, and saves it for later.*

1.  **Draft:** User adds a generic "AutoBox" device and adds pins manually.
2.  **Save:** User right-clicks the device -> **"Save to Component Library..."**
3.  **Metadata:** A dialog asks for a **Filename** (e.g., `Haltech_Elite_2500`) and **Category**.
4.  **Result:** A stripped-down version (no X/Y, no Instance ID) is saved to `data/library/devices/`.

### 2.2. The "Top-Down" Workflow (Device Creator Wizard)
*User imports a datasheet/SVG to create a photorealistic connector.*

1.  **Start:** Tools -> **Create Custom Device**.
2.  **Import:** User selects an SVG file (e.g., `dtm04.svg`).
3.  **Scale:** User verifies/sets the physical width (e.g., "18mm").
4.  **Pinning:** User uses the **"Pin Placement Tool"** to define pins.
    * *Click 1 (The Head):* Snaps strictly to the 20px Grid. This is where wires attach.
    * *Click 2 (The Tail):* Snaps to the SVG geometry. This is where the pin physically exits the connector.
    * *Visual:* A "Leader Line" is drawn between Head and Tail.
5.  **Save:** The SVG data + Pin Logic is bundled into a single YAML file.

### 2.3. The "Usage" Workflow
1.  **Browse:** User opens the **Library Tab** in the main window.
2.  **Insert:** User drags "Deutsch DTM-4" onto the canvas.
3.  **Behavior:** A new `DeviceItem` appears with the SVG background and all pins pre-populated and spatially arranged.

---

## 3. Data Architecture

### 3.1. File Structure
Library parts are standard YAML files stored in a dedicated directory.

```text
TalusTrace/
└── data/
    └── library/
        └── devices/
            ├── generic_relay.yaml
            └── deutsch_dtm04.yaml
            
3.2. YAML Schema (CustomDeviceDef)
We extend the existing data model to support embedded SVGs and complex pin geometry.

YAML

# data/library/devices/deutsch_dtm04.yaml
library_id: "dtm04_4p"
label: "Deutsch DTM 4-Pin"
category: "Connectors"
type: "CustomSymbol"  # vs "AutoBox"

# Physical Dimensions (for selection box & collision)
dimensions:
  width: 40
  height: 60

# Embedded SVG (Self-contained portability)
svg_content: |
  <svg viewBox="0 0 100 150">
    <path d="..." stroke="black" fill="gray"/>
  </svg>

# Pin Definitions
pins:
  - id: "1"
    label: "Power"
    # HEAD: The Wiring Point (Grid Relative)
    x: 0
    y: 20
    side: "left"
    # TAIL: The Physical Point (SVG Relative)
    anchor_x: 15.5
    anchor_y: 22.0
    show_leader: true

  - id: "2"
    label: "Ground"
    x: 0
    y: 40
    side: "left"
    anchor_x: 15.5
    anchor_y: 42.0
    show_leader: true
4. Technical Implementation
4.1. Backend Updates (backend/models.py)
Pin Model Update: Add optional fields for the "Tail" coordinates.

Python

class Pin(BaseModel):
    # ... existing fields ...
    anchor_x: Optional[float] = None
    anchor_y: Optional[float] = None
Device Model Update: Add support for SVG content.

Python

class Device(BaseModel):
    # ... existing fields ...
    svg_content: Optional[str] = None  # Raw XML string
4.2. Frontend Updates (frontend/items.py)
PinItem Update:

Modify set_visual_geometry (or create set_geometry) to handle the Head-to-Tail offset.

If anchor_x/y are present, draw a QGraphicsLineItem (Leader) from (0,0) (Head) to mapFromScene(anchor) (Tail).

DeviceItem Refactor:

Base Class: Handle selection, movement, and context menus.

AutoBoxItem (Current): Draws drawRoundedRect and calculates size dynamically.

SvgDeviceItem (New):

Uses QtSvg.QGraphicsSvgItem to render the svg_content.

Instantiates PinItems at explicit x,y coordinates rather than auto-layout.

4.3. Application Logic (frontend/app.py)
Library Manager:

Scan data/library/devices/*.yaml on startup.

Populate a QTreeWidget or QListWidget in a new Dock/Tab.

Implement Drag-and-Drop instantiation.

Device Creator Wizard:

A modal QDialog or separate QMainWindow mode.

Canvas: A simplified HarnessCanvas with Grid.

State Machine: STATE_IMPORT -> STATE_SCALE -> STATE_PINNING.

5. Development Phases
Phase 1: The Data Layer & Library Logic
[ ] Update Pydantic models in backend/models.py.

[ ] Create backend/library.py to handle loading/saving YAML parts.

[ ] Implement "Save to Library" context menu on existing devices.

Phase 2: SVG Rendering & Pin Leaders
[ ] Create SvgDeviceItem class using hardcoded SVG data for testing.

[ ] Update PinItem to support Head/Tail leader lines.

[ ] Verify grid snapping works for Heads while Tails remain fixed to the SVG.

Phase 3: The Wizard & UI
[ ] Build the "Library" Dock Widget.

[ ] Build the "Device Creator" Wizard dialog.

[ ] Implement SVG file import and scaling logic.
