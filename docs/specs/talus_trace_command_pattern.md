# TalusTrace Command Pattern Specification

## Overview
To ensure a robust Undo/Redo system and consistent application state, all model-modifying actions must be encapsulated in `Command` objects. Tools and UI widgets must NEVER modify the `Harness` directly; they must push commands to the `UndoStack`.

## The Contract

### 1. Base Command Structure
Every command must inherit from `BaseCommand` and implement:
* `execute()`: Performs the action and saves the *inverse* state needed for undo.
* `undo()`: Reverts the action using the saved state.
* `redo()`: Re-applies the action (usually calls `execute`).
* `merge_with(other)`: (Optional) Allows merging sequential updates (e.g., dragging a slider generates 100 events; we want 1 undo step).

### 2. The Undo Stack (`infra.undo_stack`)
The `Context` holds a global `UndoStack`.
* `push(command)`: Executes the command and adds it to the history.
* `undo()`: Pops the pointer back and calls `command.undo()`.
* `redo()`: Pushes the pointer forward and calls `command.redo()`.

### 3. Required Commands (Phase 5)
| Action | Command Class | Data Stored |
| :--- | :--- | :--- |
| **Move Item** | `MoveCommand` | Item IDs, `start_pos`, `end_pos` |
| **Create Wire** | `CreateWireCommand` | New Wire Object (snapshot) |
| **Delete** | `DeleteCommand` | List of Objects (serialized snapshot) |
| **Twist** | `TwistCommand` | List of Wire IDs to group, new `TwistedPair` ID |
| **Property Change** | `UpdatePropertyCommand` | Object ID, Field Name, `old_value`, `new_value` |

## Implementation Rules
1.  **Snapshotting:** Commands must store copies of data, not references. If you delete an object, the `DeleteCommand` must hold a full serialized copy of it to restore it later.
2.  **Granularity:** A "Mouse Release" ends a command. A "Mouse Drag" should update a temporary visual, but only push the final command on release.
3.  **Dirty Flag:** Pushing a command automatically sets `context.is_dirty = True`. Undoing back to the save point sets `is_dirty = False`.

## Example Usage
```python
# GOOD
cmd = MoveCommand(device_ids=["D1"], delta=(10, 0))
context.undo_stack.push(cmd)

# BAD
device.x += 10
```