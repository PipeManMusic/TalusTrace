# Talus Trace Implementation Map: The Command Pipeline

## 1. Overview
This map defines the strict data flow for user interactions. To prevent "Action not implemented" errors and "Broken Undo" bugs, **ALL** state-changing actions must follow this 5-step pipeline.

**The Golden Rule:** The UI (`.py` files in `ui/`) must **NEVER** import or modify `core` models directly. It must only fire Command IDs.

---

## 2. The Pipeline Trace

### Phase 1: The Trigger (Configuration)
**File:** `resources/config/ui_layout.yaml`
**Responsibility:** Defines *WHAT* the user can click and *WHICH* Command ID it fires.

* **Input:** User clicks "Place Generic Device" in the Toolbar.
* **Definition:**
    ```yaml
    toolbar:
      items:
        - command: "tool.add_generic_device"
          icon: "device.svg"
    ```
* **Implementation:** `ui/layout_manager.py` reads this line.
* **Code artifact:** Creates a `QAction`.
* **Signal Connection:** `action.triggered.connect(lambda: registry.execute("tool.add_generic_device"))`

### Phase 2: The Router (Registry)
**File:** `api/actions.py`
**Responsibility:** Maps the string `"tool.add_generic_device"` to a specific Python function.

* **Mechanism:** The global `registry` singleton.
* **Lookup:** Checks internal dictionary `_actions`.
* **Failure Mode:** If ID is missing, prints `>> Action 'x' invoked but not implemented.`
* **Success:** Calls the registered function, passing the `context`.

### Phase 3: The Transaction (The Action Function)
**File:** `api/commands/*.py` (e.g., `api/commands/device.py` or `tools/placement_tool.py`)
**Responsibility:** Prepares the data and **Instantiation of the Command Object**.

* **Crucial Logic:** This function does **NOT** modify the model directly.
* **Correct Pattern:**
    ```python
    @register_action("tool.add_generic_device")
    def add_device_action(context):
        # 1. Prepare Data (Factory Logic)
        new_dev = Device(id=..., meta=...)
        
        # 2. Create Command Object
        cmd = AddDeviceCommand(new_dev)
        
        # 3. Push to Stack (Executes automatically)
        APIManager.get_instance().context.undo_stack.push(cmd)
    ```

### Phase 4: The Execution (Command Pattern)
**File:** `infra/undo_stack.py` & `api/commands/device.py`
**Responsibility:** The actual state change.

* **Base Class:** `BaseCommand`
* **Method `execute()`:**
    1.  **Mutate:** `api.context.harness.devices.append(self.device)`
    2.  **Notify:** `api.dispatch("model_changed", {"action": "add", "item": self.device})`
* **Method `undo()`:**
    1.  **Revert:** `api.context.harness.devices.remove(self.device)`
    2.  **Notify:** `api.dispatch("model_changed", {"action": "remove", "item": self.device})`

### Phase 5: The Notification (The Loop Close)
**File:** `api/manager.py`
**Responsibility:** Broadcasting the change to the Dumb UI.

* **Event:** `"model_changed"`
* **Subscribers:**
    1.  **`ui/panels/project_browser.py`**: Rebuilds the tree list.
    2.  **`ui/canvas.py`**: Redraws the scene.
    3.  **`ui/panels/properties.py`**: Refreshes if the modified item was selected.

---

## 3. Implementation Checklist (Next Session)

We will audit `api/commands/` against this map. Any function violating Phase 3 (modifying data without a Command Object) must be refactored.

### Priority Fixes:
| Command ID | Status | Violation | Fix Strategy |
| :--- | :--- | :--- | :--- |
| `tool.add_generic_device` | **BROKEN** | `PlacementTool` appends to list directly. | Switch to `AddDeviceCommand`. |
| `edit.delete` | **PARTIAL** | Modifies list directly in `api/commands/edit.py`. | Create `DeleteItemsCommand`. |
| `edit.rotate_cw` | **PARTIAL** | Modifies `.rotation` directly. | Create `RotateItemsCommand`. |
| `edit.update_property` | **BROKEN** | `PropertyPanel` calls `setattr` directly. | Ensure `UpdatePropertyCommand` is used. |
| `view.toggle_*` | **OK** | Direct UI manipulation is allowed for View actions (no model change). | No change needed. |

---

## 4. Testing The Pipeline
**How to verify without guessing:**

1.  **Trace Log:**
    * Add `print(f"Command Executing: {self.description}")` inside `BaseCommand.execute`.
2.  **Test:**
    * Perform Action (e.g., Add Device).
    * **Check:** Did "Command Executing" print?
        * **NO?** -> You broke Phase 3 (Direct mutation).
        * **YES?** -> Undo Stack is safe.
3.  **Test Undo:**
    * Press `Ctrl+Z`.
    * **Check:** Did the item disappear?
        * **NO?** -> `undo()` implementation in Phase 4 is buggy.