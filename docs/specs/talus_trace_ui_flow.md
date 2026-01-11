# Talus Trace UI Flow & Architecture Specification

## 1. The Core Philosophy
The Talus Trace UI follows a strict **Unidirectional Data Flow (Redux/Flux-style)** pattern adapted for PyQt.

1.  **The UI is Dumb:** It never calculates, it never mutates, and it never holds state. It only displays what the **Core** tells it to.
2.  **The API is the Gatekeeper:** The UI can only talk to the Core via the `APIManager`. Direct imports from `ui/` to `core/` are forbidden (except for type checking).
3.  **Commands are the only Writers:** The only way to change data is to execute a **Command** via the **Registry**.

---

## 2. The Global Architecture Map

```text
[ USER INPUT ]
      |
      v
[ UI LAYER ] (Views, Buttons, Canvas)
      |
      |  (1) Triggers Action ID ("edit.delete")
      v
[ API REGISTRY ]
      |
      |  (2) Maps ID to Function
      v
[ COMMAND OBJECT ] (Transaction)
      |
      |  (3) Executes & Pushes to Undo Stack
      v
[ CORE MODEL ] (Source of Truth)
      |
      |  (4) Mutates State (Devices, Wires)
      |
      +---> [ LIBRARY MANAGER ] (Read-Only Ref)
      |
      v
[ API MANAGER ] (Dispatcher)
      |
      |  (5) Dispatches Event ("model_changed")
      v
[ UI SUBSCRIBERS ]
      |
      +---> [ Project Browser ] -> Rebuilds Tree
      +---> [ Properties Panel ] -> Updates Fields
      +---> [ Canvas ] -> Redraws Scene
```

## 3. Component Responsibilities

### UI Layer (`ui/`)
**Role:** Visual presentation only.

**Strict Rule:** No business logic. No file I/O. No `setattr` on models.

**Inputs:** User clicks, Keys, API Events.

**Outputs:** Calls to `registry.execute()`.

### API Layer (`api/`)
**Role:** Traffic controller and Service locator.

**Strict Rule:** Stateless routing.

**Components:**
- **APIManager:** The Singleton "Main Bus".
- **ToolManager:** The State Machine for interaction.
- **ActionRegistry:** The Command Lookup Table.

### Core Layer (`core/`)
**Role:** Business Logic and Data Storage.

**Strict Rule:** Pure Python. No Qt dependencies. Unaware of the UI.

**Components:**
- **ProjectContext:** The Database.
- **LibraryManager:** The Catalog (Read-Only).
- **Logic Engines:** The Rules (Auto-routing, validation).


## 4. The Four Pillars of Implementation

To implement any feature, you must satisfy all four pipelines defined in `docs/maps/`:

1. **Initialization** ([initialization.md](../../maps/initialization.md))  
      *Question:* "How does this feature load on startup?"
      - Check: Does it require a Manager? Does it need a YAML config? Is it registered in `__init__`?

2. **The Command Pipeline** ([command_pipeline.md](../../maps/command_pipeline.md))  
      *Question:* "How does the user trigger this?"
      - Check: Is there an Action ID? Is there a Command Class? Does it support Undo?

3. **The Tool Lifecycle** ([tool_lifecycle.md](../../maps/tool_lifecycle.md))  
      *Question:* "Does this require mouse interaction?"
      - Check: Is it a Tool? Does it implement start/deactivate? Does it clean up its ghost items?

4. **Data Flow** ([data_flow.md](../../maps/data_flow.md))  
      *Question:* "How does the user see the result?"
      - Check: Does it dispatch an event? Does the UI subscribe to that event? Does the UI clear/reload correctly?


## 5. Verification Checklist (The "Definition of Done")

Before marking any UI task as complete, verify:

- [ ] **No Direct Mutation:** Search for `setattr` or assignment (`=`) in `ui/*.py`. If found, refactor to a Command.
- [ ] **Undo Support:** Press Ctrl+Z. Does the state revert perfectly?
- [ ] **Visual Sync:** Open a second panel (e.g., Browser). Does it update automatically when you change something in the Canvas?
- [ ] **Restart Safe:** Close and reopen the app. Does the layout persist/restore without crashing?