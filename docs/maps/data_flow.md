# Talus Trace Implementation Map: The Data Flow Pipeline

## 1. Overview
This map defines the "Read Path" of the application. It ensures that **every** change in the backend (Core) is instantly and accurately reflected in the frontend (UI).

**The Golden Rule:** The UI (`.py` files in `ui/`) must **NEVER** poll for data or maintain its own internal state copies. It must **ONLY** render what the API provides via events.

---

## 2. The Pipeline Trace

### Phase 1: The Mutation (The Source of Truth)
**File:** `core/models.py`, `core/device.py`, `core/harness.py`
**Responsibility:** The data changes here, usually driven by a Command (see *Command Pipeline*).

* **Trigger:** A Command executes (e.g., `AddDeviceCommand.execute()`).
* **Action:** The Python object is modified in memory.
    ```python
    # core/harness.py
    self.devices.append(new_device)
    ```
* **Requirement:** The mutation MUST be followed immediately by a notification in the Command.

### Phase 2: The Dispatch (The Broadcast)
**File:** `api/manager.py`
**Responsibility:** Notifies the rest of the system that the Truth has changed.

* **Mechanism:** `api.dispatch(event_type, event_data)`
* **Key Event Types:**
    * `"model_changed"`: Structural changes (add/remove device, wire, etc.).
        * *Payload:* `{"action": "add", "item": <obj>}`
    * `"selection_changed"`: Focus changes (user clicked something).
        * *Payload:* `{"selection": [<list of models>]}`
    * `"property_updated"`: Detail changes (renamed, moved).
        * *Payload:* `{"item": <obj>}`

### Phase 3: The Consumption (The View Updates)
Each UI component subscribes to specific events and **completely refreshes** its relevant state.

#### A. The Project Browser (Tree View)
**File:** `ui/panels/project_browser.py`
**Subscription:** `model_changed`
**Logic:**
1.  Receives event.
2.  Calls `self.refresh()`.
3.  **Re-reads** `api.context.harness.devices`.
4.  Rebuilds the `QTreeWidget` items from scratch (or intelligently updates delta).
* *Correction needed:* Currently often ignored by `PlacementTool`.

#### B. The Properties Panel (Detail View)
**File:** `ui/panels/properties.py`
**Subscription:** `selection_changed`, `property_updated` (via `model_changed` wrapper)
**Logic:**
1.  Receives `selection_changed`.
2.  Gets the first item from the payload.
3.  **Inspects `item.meta`**.
4.  Dynamically generates input fields for "Manufacturer", "Width", etc.
* *Correction needed:* Needs to support dynamic metadata loop.

#### C. The Canvas (Visual View)
**File:** `ui/canvas.py`
**Subscription:** `model_changed`
**Logic:**
1.  Receives event.
2.  If `action == "add"`: Creates a new `DeviceItem` for the model.
3.  If `action == "remove"`: Finds the `DeviceItem` associated with the model and calls `scene.removeItem()`.
4.  If `action == "move"` (or refresh): Updates positions.

---

## 3. Implementation Checklist

We will audit these files to ensure they adhere to the "Push" model, not "Pull" or "Sync".

### Priority Fixes:
| Component | Status | Violation | Fix Strategy |
| :--- | :--- | :--- | :--- |
| **Project Browser** | **BROKEN** | Does not listen to `model_changed` (or event isn't fired). | Implement `subscribe("model_changed", self.refresh)`. |
| **Properties Panel** | **PARTIAL** | Hardcoded fields (ID, X, Y) only. | Implement iteration over `device.meta` to generate fields. |
| **Library Panel** | **BROKEN** | Loads files directly in UI. | Move loading to `core/library_manager.py`; UI calls `api.library.get_parts()`. |
| **Canvas** | **OK** | Generally updates, but needs to handle `model_changed` vs `scene.update()` distinction clearly. | Ensure `AddDeviceCommand` calls `load_harness` or specific add logic. |

---

## 4. Testing The Flow
**How to verify without guessing:**

1.  **Event Log:**
    * Add `print(f"Event Dispatched: {event_type}")` in `APIManager.dispatch`.
2.  **Test:**
    * Place a device.
    * **Check:** Did `Event Dispatched: model_changed` appear in terminal?
        * **NO?** -> Command didn't dispatch. Fix `PlacementTool` / `AddDeviceCommand`.
        * **YES?** -> Check Subscribers.
3.  **Test Listener:**
    * Add `print("Browser Refreshing...")` in `ProjectBrowser.refresh`.
    * **Check:** Did it print?
        * **NO?** -> Browser subscription is missing.