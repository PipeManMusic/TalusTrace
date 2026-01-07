# Feature Spec: Custom Devices & Device Wizard

## 1. Overview
This spec manages the lifecycle of components from "Napkin Sketches" to photorealistic, 1:1 industrial connectors.

### Core Traits
1.  **Device Promotion:** Right-click a Generic "Napkin" device to promote it to an Industrial Device, pre-populating the Wizard with existing pin data.
2.  **Ghosting:** If an SVG asset is missing, the system preserves the "Logical Skeleton" (pins and connections) as a Ghost Device.
3.  **1:1 Calibration:** The Wizard calculates a `scale_factor` to maintain physical truth (mm) on the Formboard.

## 2. Wizard Workflow
* **STATE_IMPORT:** Import 2D CAD (Future) or SVG.
* **STATE_SCALE:** Calibrate pixels to real-world millimeters.
* **STATE_PINNING:** Map "Heads" (Grid-locked wiring points) to "Tails" (Physical SVG exit points).