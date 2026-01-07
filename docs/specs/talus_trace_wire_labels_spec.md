# Feature Spec: Wire Labels & Breakout Tags

## 1. Overview
This feature allows users to attach **floating labels** to any wire in the diagram. These labels serve as critical identifiers for long wire runs or complex bundle breakouts.

### Core Goals
1.  **Path Attachment:** Labels are logically attached to a wire. If the wire moves, the label follows.
2.  **Orthogonal Sliding:** For standard wires, labels slide along the straight vertical/horizontal segments. They snap to the wire path like a bead on a string.
3.  **Dynamic Content:** Defaults to `{Wire_ID}` but can be overridden (e.g., "Fuel Pump").
4.  **Readability:** Rendered with a solid background to ensure legibility over the grid.

---

## 2. User Workflow

### 2.1. Creation
* **Action:** Right-click on a wire segment -> **"Add Label"**.
* **Result:** A label appears at that exact point on the wire.

### 2.2. Interaction
* **Slide:** User drags the label.
    * It does *not* detach from the wire.
    * It slides along the current segment (e.g., horizontal).
    * If dragged past a corner, it "turns the corner" and continues sliding along the next vertical segment.
* **Edit:** Double-click to rename.

### 2.3. Deletion
* **Action:** Select Label -> Delete. (Removes label only).
* **Dependency:** Deleting the Wire removes the Label automatically.

---

## 3. Data Architecture

### 3.1. Schema Updates (`backend/models.py`)

```python
class WireLabel(BaseModel):
    id: str
    text: Optional[str] = None
    
    # Position is stored as a percentage (0.0 to 1.0) of the total wire length.
    # This ensures that if the wire grows/shrinks, the label stays relatively positioned.
    t_pos: float = 0.5 
    
    visible: bool = True

class Wire(BaseModel):
    id: str
    # ... existing fields ...
    labels: List[WireLabel] = []
```
## 4. Technical Implementation
### 4.1. The Label Item (frontend/items.py)
```python
Pythonclass WireLabelItem(QGraphicsItem):
    def __init__(self, label_model, parent_wire_item):
        super().__init__(parent=parent_wire_item)
        self.model = label_model
        self.wire_item = parent_wire_item
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        
        # Calculate initial X/Y based on t_pos
        self.update_position_from_model()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # INTERCEPT MOVEMENT (The "Bead on a String" Logic)
            mouse_pos = value
            
            # 1. Get the Orthogonal Path (List of QPointF)
            # Standard wires are just a list of points: [Start, Elbow1, Elbow2, End]
            path_points = self.wire_item.get_path_points() 
            
            # 2. Find closest point on this Polyline to the mouse
            # (Math: Point-to-Segment distance)
            new_pos_on_wire, new_t = self.calculate_snap_to_polyline(path_points, mouse_pos)
            
            # 3. Update Model
            self.model.t_pos = new_t
            
            # 4. Return the constrained position
            return new_pos_on_wire
            
        return super().itemChange(change, value)
```
### 4.2. Orthogonal Math HelperWe treat the wire as a single line with total length $L$.To Draw:Calculate $L_{target} = t\_pos \times TotalLength$.Iterate through segments ($P_0 \to P_1$, $P_1 \to P_2$).Subtract segment length from $L_{target}$ until it fits in the current segment.Interpolate linearly on that segment to find the $(x,y)$ coordinate.To Drag (Reverse):Find which segment the mouse is closest to.Project the mouse point onto that segment.Calculate the distance from the wire start to that projected point.$t\_pos = \frac{Distance}{TotalLength}$.

## 5. Development 
### PhasesPhase 1: 
Data & Rendering[ ] 
Update Wire model to include labels list.[ ] 
Implement WireLabelItem drawing (Text with background rect).[ ] 
Add get_path_points() to WireItem to expose the polyline geometry.
### Phase 2: Orthogonal Sliding Logic[ ] 
Implement calculate_snap_to_polyline:Logic to find the nearest point on a multi-segment line.Logic to convert that point into a normalized t value (0.0 - 1.0).[ ] 
Connect itemChange to enforce this constraint during drag.Phase 3: UI Integration[ ] 
Context Menu: "Add Label" inserts a label at t=0.5 (middle).[ ] 
Double-click handler for text editing.