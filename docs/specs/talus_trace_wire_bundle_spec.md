# Feature Spec: Wire Bundles (Inferred Topology)

## 1. Overview
**Wire Bundles** represent consolidated runs of wires. In Talus Trace, bundles are no longer manually created; they are **Emergent Entities** inferred from overlapping wire paths on the grid.

### Core Traits
1.  **Inferred Topology:** Created automatically whenever multiple wires or Twisted Pairs share a grid segment.
2.  **Dynamic Sizing:** Thickness is calculated using the industrial formula: $D \approx 1.15 \times \sqrt{\sum d^2}$.
3.  **Visual Modes:**
    * **Diagram View:** Represented as a clean, consolidated trunk line.
    * **Formboard Mode:** Expanded to true physical diameter based on the standard library.

## 2. Performance
* **Memoized Calculation:** Sizing results are stored in the Calculation Cache YAML to ensure a snappy UI.