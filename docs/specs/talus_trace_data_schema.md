# Talus Trace Data & Serialization Specification

## 1. Core Principles
* **Source of Truth:** All internal measurements are stored in **Millimeters (mm)**. The UI layer translates these for display based on user preference.
* **Immutability & Commands:** State is updated via serializable Command transactions to support collaborative synchronization and AI-intent tracking.
* **Strict Spec Isolation:** To maintain performance, an entity can only reference one Engineering Standard YAML at a time.

## 2. Global Models

### 2.1. The Command Transaction
Every change is wrapped in this model to support the "Stream of Truth" and Distributed Computation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `command_id` | `str` | UUID for the transaction. |
| `type` | `str` | e.g., `MOVE_NODE`, `ASSIGN_SPEC`, `PROMOTE_DEVICE`. |
| `target_id` | `str` | The UUID of the entity being modified. |
| `payload` | `dict` | The delta data (e.g., `new_pos: [100, 200]`). |
| `intent_metadata` | `dict` | **AI Context:** Optional field describing *why* the change was made. |
| `revision` | `int` | Current revision number for Optimistic Locking. |

### 2.2. The Calculation Promise
Used for non-blocking, distributed engineering math (e.g., bundle sizing).

| Field | Type | Description |
| :--- | :--- | :--- |
| `job_id` | `str` | Unique ID for the computation task. |
| `status` | `str` | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`. |
| `result_cache_path` | `str` | Path to the memoized YAML result file. |

## 3. Entity Models

### 3.1. Device Model
Supports the lifecycle from "Napkin Sketch" to 1:1 Industrial Device.

| Field | Type | Description |
| :--- | :--- | :--- |
| `is_generic` | `bool` | True if this is a temporary DIY "Napkin" device. |
| `is_ghost` | `bool` | True if the physical asset (SVG) is missing; triggers ghost rendering. |
| `library_id` | `str` | Reference to the master YAML in the library. |
| `promotion_source_id` | `str` | Links an industrial device back to its generic ancestor. |

### 3.2. Wire & Bundle Model
Supports inferred topology and industrial standards.

| Field | Type | Description |
| :--- | :--- | :--- |
| `standard_id` | `str` | Points to a specific isolated YAML standard (e.g., `SAE_J1128`). |
| `status` | `str` | `UNDEFINED` (Draft mode) or `SPECIFIED` (Industrial mode). |
| `z_index` | `int` | Explicit layer for handling crossovers. |
| `is_terminated` | `bool` | If True, triggers terminal-to-cavity fit audits. |

## 4. Concurrency & Integrity
### 4.1. Optimistic Locking
* Reject a command if the incoming `base_revision` is less than the current `entity.revision`.
### 4.2. Ghost Handling
* Missing devices on load generate a `GhostDevice` with a Red Dashed Outline.
* Logical pins and connections are preserved to allow routing to continue.