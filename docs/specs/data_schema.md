# Talus Trace Data & Serialization Specification

## 2. Concurrency
### 2.1. Optimistic Locking
* Reject command if `entity.revision > base_revision`.

## 2.2. Ghost Handling
* Missing devices on load generate `GhostDevice` with Red Dashed Outline.