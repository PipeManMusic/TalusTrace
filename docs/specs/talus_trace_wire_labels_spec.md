# Feature Spec: Wire Labels & Breakout Tags

## 1. Overview
This feature allows users to attach floating labels to any wire. Labels serve as critical identifiers for long wire runs or complex bundle breakouts, maintaining visibility across both Diagram and Formboard modes.

### Core Traits
1.  **Path Attachment:** Labels are logically attached to a wire entity in the Core. If the wire moves, the label coordinates update automatically.
2.  **Orthogonal Sliding:** Labels "snap" to the wire path like a bead on a string, sliding only along the valid segments of the wire polyline.
3.  **Dynamic Content:** Content is driven by Core metadata (defaulting to `{Wire_ID}`).
4.  **LOD Awareness:** Labels respect the `lod_threshold_scale` defined in `theme_tokens.json`, hiding automatically when zoomed out to prevent clutter.

## 2. User Workflow

### 2.1. Creation
* **Action:** Right-click on a wire segment -> **"Add Label"**.
* **Result:** The UI sends an `ADD_LABEL` Command to the API. A label appears at the clicked `t_pos` (percentage along the wire).

### 2.2. Interaction
* **Slide:** User drags the label. The UI constrains movement to the wire's current segments.
* **Edit:** Double-clicking triggers a UI dialog; saving emits an `UPDATE_LABEL_TEXT` Command to the Core.

### 2.3. Deletion
* **Dependency:** Deleting a Wire entity triggers a cascading deletion of all associated Label entities in the Core.

## 3. Data Architecture (Core Layer)

```python
class WireLabel(BaseModel):
    id: str
    text: Optional[str] = None
    # Position stored as 0.0 to 1.0 (start to end of wire)
    # Actual mm position is calculated by the Core
    t_pos: float = 0.5 
    visible: bool = True
    status: str = "UNDEFINED" # Supports Draft-First workflow
```
## 4. Technical Implementation (UI Layer)4.1. The Label ItemPythonclass WireLabelItem(QGraphicsObject):
``` python   
    def __init__(self, label_model, parent_wire_item):
        super().__init__(parent=parent_wire_item)
        self.model = label_model
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # 1. Capture user intent (mouse position)
            # 2. Ask API to calculate nearest t_pos on wire in mm
            # 3. Emit MOVE_LABEL command
            # 4. Return the snapped pixel coordinate provided by API
            pass
        return super().itemChange(change, value)
```
## 5. Mathematical Logic (Core Calculation)Total Length ($L$): Core calculates total wire length in mm by summing all segments.Target Position ($L_{target}$): $L_{target} = t\_pos \times L$.Point Interpolation: The Core iterates through segments until the cumulative length reaches $L_{target}$, then interpolates the $(x, y)$ coordinate in mm.UI Update: The UI Layer receives the mm coordinate and applies the physical_scale from theme_tokens.json to render the label.