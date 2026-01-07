# Architecture Spec: Core Layer
**Status:** Holy (Zero external dependencies)

## 1. Responsibilities
* **Data Integrity:** Primary owner of Pydantic models for Devices, Wires, Pins, and Bundles.
* **Engineering Truth:** Internal storage of all spatial data in **Millimeters (mm)**.
* **Logical Validation:** Execution of Inferred Topology (bundling) and sizing algorithms.

## 2. Pydantic Model Requirements
* **Device:** Must support `is_generic` and `is_ghost` states.
* **Wire:** Must support an `UNDEFINED` status for draft-first workflows.
* **Pins:** Must maintain a logical "Head" (wiring point) and physical "Tail" (SVG point).

## 3. Engineering Algorithms
* **Bundle Sizing:** $D = 1.15 * \sqrt{\sum d^2}$.
* **Coalescence:** Hashing of wire segments by grid-coordinates to infer bundles.