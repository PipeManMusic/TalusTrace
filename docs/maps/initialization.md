# Talus Trace Implementation Map: The Initialization Pipeline

## 1. Overview
This map defines the "Boot Sequence" of the application. The strict order of operations guarantees that **Core Services** (Database, Library, Undo) are fully ready before the **UI** ever attempts to draw them.

**The Golden Rule:** The API is the "Motherboard". It must be powered on and fully loaded (Phases 1 & 2) before the "Monitor" (UI) is plugged in (Phase 3).

---

## 2. The Lifecycle Trace

### Phase 1: The Core Foundation (Headless)
**File:** `api/manager.py` (`__init__`)
**Trigger:** `ui/app.py` calls `APIManager.get_instance()`
**Responsibility:** Loading pure Python data structures.

1.  **Singleton Creation**: `APIManager` instance created.
2.  **Context**: `ProjectContext` initialized (holds the empty Harness model).
3.  **Library (THE FIX)**:
    * `self.library = LibraryManager("resources/library/parts.yaml")`
    * **Action:** `LibraryManager` (in `core/`) reads and parses the YAML immediately.
    * **Result:** `self.library.parts` is populated with Dicts.
    * *Note:* If YAML is missing, it logs a warning but keeps the app alive.
4.  **Undo Stack**: `self.undo_stack` created.

### Phase 2: The Service Layer (Headless)
**File:** `api/manager.py`
**Trigger:** Continued from Phase 1.
**Responsibility:** Preparing the logic engines.

1.  **Tool Manager**: `self.tool_manager` initialized.
    * Registers `SelectTool`, `PlacementTool`, etc.
    * *Critical:* Tools are instantiated but **not** started.
2.  **Input System**: `self.input_system` initialized.
    * *Note:* It is created here but not yet "installed" because the Canvas doesn't exist.

### Phase 3: The View Assembly (The Container)
**File:** `ui/main_window.py` (`__init__`)
**Trigger:** `ui/app.py` instantiates `MainWindow()`
**Responsibility:** Building the visual shell *around* the existing Core.

1.  **API Registration**: `api.main_window = self` (The Link).
2.  **Canvas**: `self.canvas = HarnessCanvas(self)`.
3.  **Input Installation**: `api.input_system.install(self.canvas)`.
    * *Action:* Event filters are attached to the Qt Viewport.

### Phase 4: The Configuration (The Layout)
**File:** `ui/layout_manager.py`
**Trigger:** `MainWindow` calls `LayoutManager`
**Responsibility:** Defining *where* things go.

1.  **Load YAML**: `resources/config/ui_layout.yaml`.
2.  **Load Actions**: `resources/config/actions.yaml`.
3.  **Construct Menus**: Build `QMenuBar` based on config.
4.  **Construct Toolbar**: Build `QToolBar` based on config.

### Phase 5: The Content (The Subscribers)
**File:** `ui/main_window.py` (`_create_docks`)
**Trigger:** `MainWindow` finishes layout.
**Responsibility:** Creating "Dumb Views" that ask the API for data.

1.  **Project Browser**:
    * Created: `ProjectBrowser()`
    * **Subscription**: `subscribe("model_changed")` (Listening).
    * **Initial Fetch**: Calls `api.context.harness` to populate initial tree.
2.  **Library Panel (THE FIX)**:
    * Created: `LibraryPanel()`
    * **Logic**: Does **NOT** load YAML.
    * **Initial Fetch**: Calls `api.library.get_parts()`.
    * **Render**: Populates tree from the API data.
3.  **Properties Panel**:
    * Created: `PropertyPanel()`
    * **Subscription**: `subscribe("selection_changed")` (Listening).

### Phase 6: The Handshake (Ready State)
**File:** `ui/app.py`
**Trigger:** `window.show()`
**Responsibility:** Opening the curtain.

1.  `registry.action_triggered.connect(status_bar_update)`.
2.  `window.show()`.
3.  **App Event Loop Starts.**

---

## 3. Implementation Checklist

We will audit the startup files to ensure `LibraryManager` is moved to Core and UI file IO is removed.

### Priority Fixes:
| Component | Status | Violation | Fix Strategy |
| :--- | :--- | :--- | :--- |
| **Library Manager** | **MISSING** | `core/library_manager.py` does not exist. | Create it to handle YAML parsing. |
| **API Init** | **UPDATE** | `APIManager` does not init Library. | Add `self.library = LibraryManager()` to `api/manager.py`. |
| **Library Panel** | **BROKEN** | `ui/panels/library.py` imports `yaml`. | **DELETE** `yaml` import. Replace file loading with `api.library.get_parts()`. |
| **Input System** | **RISK** | Circular dependency potential. | Ensure `InputSystem` is lazy-loaded or imported inside `__init__`. |

---

## 4. Testing The Boot Sequence
**How to verify without guessing:**

1.  **Trace Log:**
    * `core/library_manager.py`: `print(">> [CORE] Library Loaded (XX parts)")`
    * `ui/panels/library.py`: `print(">> [UI] Library Panel asking API for data")`
2.  **Run:** `python3 -m ui.app`
3.  **Check Output:**
    * **Success:** `[CORE]` prints **BEFORE** `[UI]`.
    * **Failure:** If `[UI]` prints first, or if `[CORE]` never prints, the pipeline is broken.