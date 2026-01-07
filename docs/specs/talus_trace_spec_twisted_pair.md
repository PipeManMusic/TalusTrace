# Feature Spec: Twisted Pair (Updated)

## 1. Overview
The **Twisted Pair** is an atomic entity representing two signals twisted together. In the "Draft-First" workflow, it acts as a single "Super-Wire" in Diagram View to reduce complexity while maintaining industrial data integrity in the background.

### Core Traits
1.  **Atomic Entity:** It is a single object with two physical termini. Deleting one end removes the entire pair.
2.  **Inferred Bundling:** If a Twisted Pair's path overlaps with other wires on the grid, it logically merges into a Bundle Segment while maintaining its internal helix visual.
3.  **Signal Tunneling:** Connecting a signal (e.g., CAN_HI) to one end propagates it to the other instantly.
4.  **Drafting State:** Can exist as "Undefined" (no assigned gauge or twist rate) and will be flagged in the Audit List until specified.

## 2. Technical Architecture
* **Calculation Promise:** Twist rate and physical length calculations are offloaded to background threads.
* **Rendering:** Procedural double-helix using sine/cosine waves along a Bezier path.