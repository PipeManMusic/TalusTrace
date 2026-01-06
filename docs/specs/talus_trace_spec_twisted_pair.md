# Feature Spec: Twisted Pair (Updated)

## 1. Overview
The **Twisted Pair** (formerly Twisted Bundle) is a specialized entity representing two wires twisted together. Unlike standard wires, it functions atomically—it has two "ends" that act like devices, but they are inextricably linked. Deleting one end removes the entire entity.

### Core Traits
1.  **Atomic Entity:** It is not two devices connected by a wire; it is a single object with two physical termini.
2.  **Grid-Locked Pins:** The connection points (Pins) must always reside on the 20px grid.
3.  **Procedural Visuals:** The wire body is rendered as a double-helix pattern that follows a Bezier curve, dynamically colored based on signal assignment.
4.  **Synchronized Identity:** Changing wire properties (Color/ID) on one end instantly propagates to the other end and updates the helix visuals.

---

## 2. Visual Anatomy

### 2.1. The "Twist End" (The Head)
Each Twisted Pair has two "Heads" (Start and End).
* **The Anchor Node:** A circular control grip. This is what the user drags to move the end.
* **The Pins:** Two `PinItem`s.
    * **Position:** Strictly snapped to the 20px Grid.
    * **Orientation:** They rotate around the Anchor Node.
* **The Tails:** Short, straight "leader lines" connecting the Pin Heads to the Anchor Node.

### 2.2. The "Twist Body" (The Wire)
* **Pathing:** A smooth Bezier path connecting Anchor Node A to Anchor Node B.
* **Rendering:** Two oscillating paths (Sine and Cosine waves) generated along the normal of the main path to simulate a double helix.
* **Colors:**
    * Helix A: Inherits color from Pin 1's connected wire.
    * Helix B: Inherits color from Pin 2's connected wire.

---

## 3. User Interaction

### 3.1. Movement & Snapping
* **Drag:** User drags the **Anchor Node**.
* **Follow:** The pins move with the Anchor.
* **Snap:** While the Anchor moves freely (or snaps to grid), the **Pins** calculate their offset and strictly snap to the nearest grid intersection. This may cause the distance between Pin and Anchor to "breathe" slightly to satisfy grid constraints.

### 3.2. Rotation (Spacebar)
* **Trigger:** User selects an Anchor Node and presses `Space`.
* **Action:** The two pins rotate 90 degrees around the Anchor Node.
* **Constraint:** The new positions must be valid grid points.
    * *Example:* Horizontal (Pins at relative 0,0 and 0,20) -> Vertical (Pins at 0,0 and 20,0).

### 3.3. Atomic Deletion
* **Action:** User selects *any* part of the Twisted Pair (Wire body, Anchor, or Pins) and presses Delete.
* **Result:** The entire entity is removed: Start Pins, End Pins, and the Wire.

---

## 4. Technical Architecture

### 4.1. Data Model (`backend/models.py`)

```python
class TwistedPair(BaseModel):
    id: str
    
    # End A Configuration

    node_a: Tuple[float, float]
    rotation_a: int = 0  # 0, 90, 180, 270

    # End B Configuration
    node_b: Tuple[float, float]
    rotation_b: int = 0

    # Signal Data (Synced across the pair)
    wire_id_1: Optional[str] = None # High/Signal
    wire_id_2: Optional[str] = None # Low/Return
4.2. Frontend Implementation (frontend/twisted_pair.py)We need a custom QGraphicsItem that manages the sub-items.Pythonclass TwistedPairItem(QGraphicsObject):
    def __init__(self, model):

        # 1. Create Anchors
        self.anchor_a = TwistAnchorItem(self, model.node_a)
        self.anchor_b = TwistAnchorItem(self, model.node_b)
        self.helix = DoubleHelixPathItem(self)

        # Pins & Leaders are now CHILDREN of the Anchors. This keeps the TwistedPairItem container clean. Grid snapping is handled by mapping scene coordinates to the anchor's local space.

    def update_layout(self):
        """
        Calculates pin positions based on Anchor Pos + Rotation + Grid Snap.
        Updates the Bezier path for the helix.
        """
        pass
        
    def sync_colors(self):
        """
        Checks the wires connected to pins_a[0] and pins_a[1].
        Updates pins_b to match.
        Updates helix colors to match.
        """
        pass
4.3. Procedural Helix RenderingTo draw the twisted look along a curve:Calculate the main Cubic Bezier path between Anchor A and Anchor B.Iterate along the path (e.g., every 5 pixels).At each point $t$, calculate the Normal Vector (perpendicular to direction).Offset two points using sin(t * frequency) and cos(t * frequency) scaled by the Normal.Connect these points to form two intertwining paths.5. Synchronization LogicThe "Sync" EventSince the twisted pair is a bridge, it must propagate identity.Event: Pin A1 receives a wire connection (e.g., Red, 18AWG, Label "CAN High").Logic:TwistedPairItem detects change on Pin A1.Updates internal model wire_id_1.Updates Pin B1 to virtually represent that same wire.Updates Helix Path A to Red.Triggers redraw.6. Development Phases (Issue Tracker)Phase 1: The Atomic Container[ ] Create TwistedPair model in backend.[ ] Create TwistedPairItem graphics container.[ ] Implement Atomic Deletion (selecting any part selects/deletes whole).Phase 2: Anchor & Pin Dynamics[ ] Implement TwistAnchorItem (The Drag Handle).[ ] Implement Pin rotation logic (Spacebar) with strict Grid Snapping.[ ] Draw "Tail" lines connecting Pins to Anchor.Phase 3: The Double Helix[ ] Implement DoubleHelixPathItem.[ ] Write algorithm to generate sine/cosine offsets along a Bezier curve.[ ] Bind colors to the wire_id state.Phase 4: Signal Propagation[ ] Implement observer logic: When a wire connects to End A, push data to End B.[ ] Ensure wire_id persists in YAML save/load.
