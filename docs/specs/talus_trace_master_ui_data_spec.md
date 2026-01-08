# Talus Trace Master Specification: UI & Data Architecture

**Status:** Approved for Phase 7
**Philosophy:**
1.  **Binary Speed:** System caches are binary blobs. Zero parsing time for massive harnesses.
2.  **Total Customization:** The UI is a "Dumb Renderer" for the `ui_layout.yaml` file. If a user wants "Delete" on the top toolbar, they add it to the YAML.
3.  **Command Registry:** Every function (`edit.move`, `view.zoom`) is a registered action that can be mapped to *any* input (Key, Mouse, Menu, Button).
4.  **Robust Defaults:** The system ships with a factory default for every configuration, so broken user configs trigger a graceful fallback, not a crash.

---

## Part 1: File Architecture (The Granular Database)

We adopt a strict separation between **User Resources** (Human-readable, Editable) and **System Cache** (Machine-optimized, Disposable).

### 1.1 The User Resources (`resources/`)

These files are version-controlled by the user and define the "Personality" of the application.

| Path | Purpose | Content Type |
| :--- | :--- | :--- |
| `config/actions.yaml` | **The Registry.** Defines commands, icons, and default hotkeys. | Key/Value Mappings |
| `config/ui_layout.yaml` | **The Interface.** Defines what commands appear in Toolbars/Menus. | Nested Lists |
| `config/theme.yaml` | **The Look.** Colors, fonts, and grid settings. | Visual Tokens |
| `library/wires.yaml` | **The Physics.** Wire gauges, resistance, OD, weight. | Physical Properties |
| `library/parts.yaml` | **The Footprints.** Connectors, splices, pins. | Part Metadata |
| `rules/*.yaml` | **The Police.** Validation logic for the Audit Engine. | Logic Expressions |

### 1.2 The System Cache (`.cache/`)

Hidden binary files for sub-millisecond startup. Git-ignored.

* **`render/*.bin`**: Pre-tessellated QPolygonF geometry (e.g., Helix points).
* **`routing/*.bin`**: Solved A* paths and spatial hashes.
* **`bom/*.bin`**: Aggregated cost/weight calculations.
* **Format:** Python `pickle` (Protocol 5) or `msgpack`.

---

## Part 2: The Action Registry Model

The application does not have hardcoded buttons. It has a **Command Bus**.

### 2.1 The Registry (`actions.yaml`)
Defines *what* can be done, not *how* it is triggered.

```yaml
commands:
  - id: "edit.move"
    label: "Move Item"
    icon: "icons/move.svg"
    tooltip: "Moves selected items (Ghost Mode)"
    default_key: "G"

  - id: "tool.measure"
    label: "Measure Distance"
    icon: "icons/ruler.svg"
    default_sequence: ["M", "E"]
2.2 The Layout Engine (ui_layout.yaml)Defines where commands appear.YAMLtoolbar:
  visible: true
  items:
    - command: "file.save"
    - separator: true
    - command: "edit.undo"
    - command: "edit.redo"

context_menu:
  device:
    - command: "edit.move"
    - command: "edit.rotate_cw"
```
## Part 3: UI Interaction Model (The "Pro" Workflow)The UI follows a Modal-Free, Noun-Verb interaction model optimized for "Two-Handed" drafting (Left hand on Home Row).

### 3.1 The "Home Row" Keymap (Left Hand)
Critical functions are mapped to the left hand's resting position (ASDF/QWER).

| Key         | Action             | Mnemonic/Logic                        |
|-------------|--------------------|---------------------------------------|
| G           | edit.move          | Grab selection (Ghost mode).          |
| Space       | edit.rotate_cw     | Space to rotate 90° CW (Thumb reach). |
| Shift+Space | edit.rotate_ccw    | Rotate 90° CCW.                       |
| D           | edit.delete        | Delete selection.                     |
| W           | tool.wire_mode     | Wire routing mode.                    |
| Esc         | cancel             | Cancel operation / Deselect.          |
| Tab         | view.toggle_props  | Toggle Properties Panel (Right side). |

### 3.2 Command Sequences (Aliases)

For less common actions, the system listens for 2-key sequences (timeout: 500ms).
Z, E → view.zoom_extents (Fit All)
Z, S → view.zoom_selected (Fit Selection)
W, A → tool.wire_add (Add Wire)

### 3.3 The "Smart Cursor"
The cursor icon changes to communicate available actions ("Affordance").
Empty Space: Arrow (Click to Select, Drag to Box-Select).
Device Body: Open Hand (Drag to Move).
Rotation Grip: Refresh Icon (Drag to Rotate).
Pin/Terminal: Crosshair (Click to start Wire).

## Part 4: Data Schema & Validation

### 4.1 The Wire Catalog (wires.yaml)Drives engineering calculations.YAMLwires:
``` yaml
  "TXL-18":
    family: "SAE J1128 TXL"
    od_mm: 2.18
    resistance_ohm_m: 0.021
    weight_g_m: 9.6
```
### 4.2 The Rules Engine (rules/)Logic-driven validation expressions.YAMLrules:
``` yaml
  - id: "ELEC_001"
    name: "Voltage Drop Limit"
    severity: "error"
    # Expression evaluated safely at runtime
    check: "((length_mm / 1000) * library.resistance * load_amps) > 1.0"
```
## Part 5: Implementation Strategy (Fail Gracefully)Startup: 

App attempts to load User Configuration from resources/.Validation: 
App checks loaded config against internal DEFAULT_CONFIG.Fallback:
If a file is missing → Use internal Default.
If a key is missing → Use internal Default for that key.
If a file is corrupt → Log error, alert user, and use internal Default.
Result: The application never crashes due to bad configuration.