# Talus Trace: Project Intent

## 1. Vision & Philosophy: "Complexity Hidden by Design"
**Talus Trace** is an industrial-grade CAD application for automotive electrical design that remains **DIY-friendly**. It bridges the gap between a "napkin sketch" wiring diagram and a production-ready manufacturing formboard. The goal is a tool where a user can focus on a clean, professional diagram, while an "Invisible Engineer" (The Core) automatically builds the underlying harness topology, sizing, and safety audits.

## 2. The Narrative Pillars
* **The Source of Truth Library:** Components begin as high-fidelity SVGs or CAD imports. The **Device Creator Wizard** allows users to map logical pins (Heads) to physical exit points (Tails).
* **Inferred Topology:** If multiple wires are snapped to the same grid line, the system understands they are a **Bundle**. Users don't "build" bundles; they emerge naturally from the drawing.
* **Atomic Sub-assemblies:** Entities like **Twisted Pairs** are treated as single "Super-Wires" in the diagram view, collapsing complexity until the 1:1 manufacturing phase.

## 3. Workflow Modes: Diagram vs. Formboard
* **Diagram View (Non-1:1):** The primary creative space. Focused on logical connectivity and "The Look." Wires overlap to form bundles, and symbols represent devices.
* **Formboard Mode (1:1):** The manufacturing "Physical Twin." The system "unfolds" the diagram into real-world dimensions (mm). Users can print "tiled" templates to create physical assembly boards.

## 4. Drafting Logic: "Draft-First" Workflow
* **Zero-Friction Creation:** Users can route an entire harness using "Undefined" states. Wires can be drawn without immediate gauge or material assignment.
* **Deferred Definition:** Undefined items are tracked in the Audit List, allowing the designer to refine engineering data only when transitioning from "Sketch" to "Specification."
* **Ghosting:** If a library asset is missing, the system preserves the "Logical Skeleton" (pins and connections) as a Ghost Device, ensuring data portability across different users.

## 5. Architectural Values: The "Core" and the API
* **The Core:** Pure Python engineering logic isolated from the UI.
* **Singleton API & Command Stream:** The UI is a visualizer that sends discrete, serializable commands (Transactions) to the Core.
* **Event-Driven & Distributed Computation:** Heavy math (sizing, audits) is treated as a serializable "Calculation Transaction." This allows tasks to be processed by local background threads or offloaded to high-performance remote servers without blocking the UI.
* **AI & Metadata Ready:** Every transaction supports intent-metadata, and audits are serialized for machine-readability, future-proofing for AI-assisted design optimization.
* **Semantic Theming & i18n:** Visuals are tied to semantic keys (not hardcoded colors) to support instant toggling between "Design Mode" and "Print Mode." The UI supports multi-language and multi-unit (Metric/Imperial) views on a single unified dataset.
* **Cached Calculation Engine:** To stay "snappy," all results (lengths, sizing, audits) are stored in memoized YAML files. The UI never "lags" because it reads pre-computed state.
* **Isolated Specification Libraries:** Each YAML validation library is restricted to a single engineering standard (SAE, ISO, etc.), ensuring O(1) lookup speeds and engineering integrity.

## 6. Signal vs. Wire: The Data Overlay
* **Signal Tunneling:** The Core tracks electrical signals through "transparent" components like Twisted Pairs or Bulkheads.
* **Multi-Standard Engine:** The system handles multiple concurrent standards, ensuring physical calculations are grounded in the specific tolerances of the chosen material spec.

## 7. The Design Audit & Resolution Engine
* **The Audit List:** Design violations are presented as a persistent, interactive punch-list serialized in YAML. Users can pan/zoom to issues and fix them through the Properties panel.
* **Dynamic Recipes:** Through **Resolution YAMLs**, the system can suggest or auto-apply "Fixes" (e.g., upgrading a gauge) to resolve audit failures.