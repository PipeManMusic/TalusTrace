# Talus Trace Implementation Map: The Tool Lifecycle

## 1. Overview
This map defines the "Interactive State" of the application. A Tool is a temporary state machine that interprets raw mouse/keyboard events into specific **Commands**.

**The Golden Rule:** Only ONE tool is active at a time. The `ToolManager` is the absolute authority on which tool handles input.

---

## 2. The Lifecycle Trace

### Phase 1: Activation (The Handoff)
**File:** `api/tool_manager.py`
**Responsibility:** Cleanly switching context.

* **Trigger:** User clicks a toolbar button -> `registry.execute("tool.wire")`.
* **Logic (`set_tool`):**
    1.  **Teardown:** Call `current_tool.deactivate()`.
        * *Must remove ghost items, reset cursor, clear temp data.*
    2.  **Swap:** Update `self.active_tool`.
    3.  **Setup:** Call `new_tool.start()`.
        * *Must set cursor, initialize state variables.*
    4.  **Notify:** Dispatch `"tool_changed"` event (UI updates toolbar highlight).

### Phase 2: Interaction (The Loop)
**File:** `ui/canvas.py` → `ui/input_system.py` → `Active Tool`
**Responsibility:** processing raw user input.

* **Raw Input:** `Canvas.mousePressEvent` -> wraps into `CanvasEvent`.
* **Routing:** `InputSystem` checks `APIManager.tool_manager.active_tool`.
* **Handlers:**
    * `on_mouse_move(event)`: Update ghost coordinates.
    * `on_mouse_press(event)`: Begin action (e.g., start wire).
    * `on_mouse_release(event)`: Finish action (e.g., drop device) OR continue (multi-step).
    * `on_key_press(event)`: Handle shortcuts specific to the tool (e.g., 'R' to rotate ghost).

### Phase 3: The Commit (The Output)
**File:** `tools/*.py`
**Responsibility:** Converting interaction into permanent model data.

* **Mechanism:** The tool **MUST** use the Command Pipeline.
* **Bad Pattern (Direct Mutation):**
    ```python
    harness.wires.append(Wire(...)) # WRONG: Bypasses Undo
    ```
* **Good Pattern (Command):**
    ```python
    cmd = AddWireCommand(new_wire)
    api.context.undo_stack.push(cmd) # RIGHT
    ```
* **Follow-up:** After commit, the tool usually stays active (for multiple placements) OR switches back to Select (single action).

### Phase 4: Deactivation (The Cleanup)
**File:** `tools/*.py` (`deactivate` method)
**Responsibility:** Leaving the scene exactly as it was found.

* **Crucial Checks:**
    * `scene.removeItem(self.ghost)` if it exists.
    * `canvas.setCursor(Qt.ArrowCursor)`.
    * Reset internal flags (`self.is_dragging = False`).
* *Common Bug:* Tool leaves a "phantom" square on the canvas because `deactivate` crashed or wasn't called.

---

## 3. Implementation Checklist

We will audit `tools/` to ensure every tool implements the `BaseTool` contract.

### Priority Fixes:
| Tool | Status | Violation | Fix Strategy |
| :--- | :--- | :--- | :--- |
| **BaseTool** | **REVIEW** | Check if `start()` and `deactivate()` are abstract or have defaults. | Ensure robust no-op defaults so subclasses don't crash. |
| **WireTool** | **CRITICAL** | Missing `start()` method. | Add `start()` (set crosshair) and `deactivate()` (reset cursor). |
| **PlacementTool** | **HIGH** | `deactivate()` might fail if ghost is already gone. | Wrap cleanup in `try/except` block. Ensure `AddDeviceCommand` is used. |
| **SelectTool** | **OK** | Generally stable, but check `deactivate` clears selection highlights if needed. | Verify cleanup logic. |

---

## 4. Testing The Lifecycle
**How to verify without guessing:**

1.  **Trace Log:**
    * Add `print(f">> Starting {self.name}")` in `start()`.
    * Add `print(f">> Stopping {self.name}")` in `deactivate()`.
2.  **Test Switch:**
    * Click "Wire" -> **Check:** "Starting Wire" prints.
    * Click "Select" -> **Check:** "Stopping Wire" THEN "Starting Select" prints.
    * *Failure:* If "Stopping" doesn't print, the manager logic is broken.
3.  **Test Cleanup:**
    * Start "Place Device" (Ghost appears).
    * Press `Esc` or Click "Select".
    * **Check:** Does the ghost disappear?
        * **NO?** -> `deactivate()` is missing scene removal logic.