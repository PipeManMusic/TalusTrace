# Feature Spec: Wire Bundles (Bulk Runs)

## 1. Overview
The **Wire Bundle** represents a consolidated run of multiple wires wrapped together (e.g., a loom or taped harness section). It functions physically like a Twisted Pair (an atomic entity with two ends) but visually represents mass and volume.

### Core Traits
1.  **Atomic Entity:** The Bundle is a single object containing two "End Devices" and a connecting "Trunk."
2.  **Dynamic Thickness:** The visual thickness of the trunk line increases automatically as more wires are added to the end connectors.
3.  **Single-Sided Fanout:** The End Devices restrict pin placement to the side *opposite* the bundle connection, ensuring a clean "Connector -> Backshell -> Loom" visual flow.
4.  **Virtual Entry Point:** Custom SVG ends use a "Virtual Pin" to anchor the bundle, keeping the graphic clean.

---

## 2. Visual Anatomy

### 2.1. The "Bundle End" (The Device)
Each Bundle has two Ends (Start and End).
* **Type A: Generic (AutoBox)**
    * **Visual:** A standard rectangular box.
    * **Constraint:** Pins are restricted to a single side (e.g., **Left**). The Bundle connects to the center of the **Right** side.
* **Type B: Custom (SVG)**
    * **Visual:** A rendered SVG (e.g., Deutsch DT connector).
    * **Pins:** Placed on the connector face (Grid Snapped).
    * **Bundle Anchor:** A specific "Virtual Pin" defined in the SVG YAML (the "Tail") where the thick bundle wire attaches.

### 2.2. The "Bundle Control Node" (The Grip)
* **Location:** Situated ~20px (1 grid unit) "back" from the Connector/Virtual Pin along the wire path.
* **Role:** This is the handle the user drags to route the bundle. It acts as the "Strain Relief" point.
* **Behavior:** Rotating the End Device rotates this node around the connector, effectively steering the bundle entry angle.

### 2.3. The "Bundle Body" (The Trunk)
* **Pathing:** Orthogonal (Right-Angle) routing with rounded corners (radius ~10px) to distinguish it from single wires.
* **Thickness:**
    * $Width = BaseWidth + (PinCount \times ScaleFactor)$
    * *Example:* Base 4px + (6 wires * 0.5px) = 7px thick.
* **Appearance:** Dark grey/black (representing tape/loom) rather than colored signal wires.

---

## 3. User Interaction

### 3.1. Creation
* **Tool:** "Create Bundle" -> Drag from Point A to Point B.
* **Default:** Creates two generic 4-pin ends connected by a thin bundle.

### 3.2. Adding Wires (The "Pass-Through" Logic)
* **Action:** User connects a Red Wire to **Pin 1** on **End A**.
* **Reaction:**
    1.  The system identifies the bundle relationship.
    2.  The system automatically highlights **Pin 1** on **End B** as the "Exit Point" for that red wire.
    3.  The Bundle Trunk thickness recalculates and grows slightly.

### 3.3. Movement
* **Drag Device:** Moving the End Device pulls the Bundle Control Node with it.
* **Drag Trunk:** Segments of the bundle body can be dragged orthogonally (just like standard wires).

---

## 4. Data Architecture

### 4.1. Schema (`backend/models.py`)

```python
class BundleEnd(BaseModel):
    # Configuration for one end of the loom
    type: str = "AutoBox" # or "CustomSVG"
    library_ref: Optional[str] = None # If SVG
    pin_count: int = 0
    node_pos: Tuple[float, float] # The Grip/Control Node position

class Bundle(BaseModel):
    id: str
    end_a: BundleEnd
    end_b: BundleEnd
    
    # The physical path of the loom
    path_points: List[Tuple[float, float]]
    
    # Metadata
    base_thickness: float = 4.0
5. Technical Implementation
5.1. BundleItem (Frontend)
A container item managing the three sub-components.

Python

class BundleItem(QGraphicsObject):
    def update_thickness(self):
        # Calculate active pins (connected wires)
        count = self.end_a_device.get_connected_pin_count()
        new_width = 4.0 + (count * 0.8)
        
        pen = QPen(Qt.black, new_width)
        pen.setJoinStyle(Qt.RoundJoin)
        self.trunk_item.setPen(pen)
5.2. The "Virtual Pin" Logic
For SVG ends, the bundle needs to know where to attach.

Standard: Center of the "Back" edge.

SVG: Look for a metadata point bundle_anchor in the YAML definition. If missing, default to bounding box center-right.

6. Development Phases
Phase 1: The Structure
[ ] Create Bundle and BundleEnd models.

[ ] Create BundleItem container.

[ ] Implement basic rendering: Two boxes connected by a fixed-width line.

Phase 2: The Logic
[ ] Implement Dynamic Thickness calculation based on pin connections.

[ ] Implement Control Node logic (the strain relief grip).

[ ] Ensure Spacebar rotation rotates the End Device and the Control Node together.

Phase 3: SVG Integration
[ ] Connect the CustomDevice logic (from the previous spec) to the Bundle Ends.

[ ] Implement the "Virtual Pin" attachment point for custom graphics.