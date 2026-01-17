# MAP Event Handling and Tool Activation

## Overview
This document describes the Model-Action-Policy (MAP) compliant event flow for UI interactions, tool activation, and command execution in the TalusTrace application. It ensures that all user actions are handled in a robust, auditable, and maintainable way.

---

## Event Flow and Responsibilities

1. **SelectionTool**
   - Acts as the entry point for all user UI interactions.
   - Handles mouse events and determines the appropriate tool or action to activate based on the context (e.g., device, elbow grip, segment grip).

2. **UI Items (e.g., ElbowGripItem, SegmentGripItem)**
   - Are passive: they do not mutate models or create commands directly.
   - On user action (e.g., mouse press), they:
     - Activate the appropriate tool via the ToolManager.
     - Pass the event context (as a `CanvasEvent`) to the tool’s `start()` method.

3. **Tools (e.g., ElbowMoveTool, SegmentMoveTool, PlacementTool)**
   - Accept the event context in `start(..., event=None)`.
   - If an event is provided, immediately begin their workflow (e.g., drag, placement).
   - Handle all business logic, model changes, and command creation.
   - Push commands to the undo stack for undo/redo support.

4. **Commands**
   - Are created and pushed by tools only.
   - Encapsulate all state changes for undo/redo.

5. **Event Context**
   - The event context (`CanvasEvent`) is always passed from UI → Tool → Command as needed.
   - No model or command logic is allowed in UI items.

---

## Example: Elbow Move Workflow

1. User clicks an `ElbowGripItem`.
2. `ElbowGripItem` activates `ElbowMoveTool` and passes the event to `start()`.
3. `ElbowMoveTool` immediately begins drag logic using the event.
4. All model changes and command creation are handled in `ElbowMoveTool` and `MoveElbowCommand`.

---

## Auditing and Compliance
- All event handling and state changes must follow this documented flow.
- UI items must remain passive and only route events.
- Tools must accept event context and handle all business/model logic.
- Commands must encapsulate all state changes for undo/redo.
- The SelectionTool must remain the starting point for all user UI interactions.

---

## Signature Example

```python
# Tool start method signature
class ElbowMoveTool:
    def start(self, wire_item, elbow_index, event=None):
        ...
```

- If `event` is provided, the tool should immediately call `on_mouse_press(event)` to begin the workflow.

---

## Policy
- Any deviation from this flow should be documented and justified in this file.
- This document should be updated whenever the event flow or tool activation logic changes.
