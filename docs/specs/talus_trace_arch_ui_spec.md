# Input Orchestration Specification

## 1. Purpose
To maintain "Engineering Grade" stability, the UI must separate raw hardware event capture (mouse/keyboard) from engineering logic (routing/moving). This ensures that the `HarnessCanvas` remains a pure renderer while the `InputSystem` acts as the central brain for user intent.

## 2. Hardware Abstraction Layer (HAL)
The `HarnessCanvas` is prohibited from executing tool logic directly. Its sole responsibility is to generate a **Unified Event Object**:

* **Coordinate Translation**: All pixel-based `QMouseEvent` data must be translated into "Engineering Space" (mm) using `mapToScene` before dispatching.
* **Context Enrichment**: The event must include the `scene_pos` (mm), the `scene_item` (hit-test result), keyboard `modifiers`, and a reference to the active `scene`.

## 3. Decentralized Dispatcher Flow
The `InputSystem` shall implement a subscriber-based dispatcher model:

1. **Capture**: `HarnessCanvas` receives a raw Qt event.
2. **Translate**: Canvas creates a `CanvasEvent` containing translated coordinates.
3. **Handoff**: Canvas calls `InputSystem.handle_canvas_event(event)`.
4. **Route**: The `InputSystem` identifies the active tool via `APIManager` and routes the event to the appropriate handler (e.g., `tool.on_mouse_press`).

## 4. State Synchronization Requirements
* **Real-Time Model Updates**: Tools receiving a dispatched event (e.g., `MoveTool`) must update the `Harness` model properties (`x`, `y`) in real-time. This ensures concurrent logic, such as `WireTool` pin-detection, always sees the most recent engineering data.
* **Command Bundling**: The dispatcher or tool must group high-frequency events (e.g., continuous mouse dragging) into single atomic `Command` objects for the `UndoStack` to prevent stack bloat.

## 5. Architectural Constraints
* **Logic Isolation**: `HarnessCanvas` methods (e.g., `mousePressEvent`) may only contain code for capture and handoff. They must not modify the `Harness` model or `UndoStack` directly.
* **Shortcut Priority**: The `InputSystem` must intercept keyboard events before they reach the canvas to handle global actions like Undo, Redo, and Tool Switching.