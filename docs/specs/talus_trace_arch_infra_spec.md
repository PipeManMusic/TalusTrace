# Architecture Spec: Infra Layer
**Status:** System Services

## 1. Responsibilities
* **Command Management:** Execution of `BaseCommand` objects and maintenance of the Undo/Redo stack.
* **Persistence:** Serializing the Core state to YAML and managing the Calculation Cache.
* **Concurrency:** Managing the Background Worker thread for non-blocking calculations.

## 2. Command Requirements
* **Atomicity:** Every `BaseCommand` must be serializable and include `intent_metadata` for AI.
* **Optimistic Locking:** Reject commands if `entity.revision > base_revision`.

## 3. Serialization Rules
* Do not manually edit JSON/YAML files; use `infra/manage_issues.py` for audit consistency.