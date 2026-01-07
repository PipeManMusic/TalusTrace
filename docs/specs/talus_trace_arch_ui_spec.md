# Architecture Spec: UI Layer
**Status:** View Layer (Qt/PySide6)

## 1. Responsibilities
* **Spatial Translation:** Mapping the Core's "Holy Millimeter" values to pixels using `theme_tokens.json`.
* **User Intent Capture:** Capturing clicks/drags and firing Commands via the API.
* **Rendering LOD:** Managing Zoom-dependent visuals (e.g., Helix vs. Hatch for Twisted Pairs).

## 2. UI Constraints
* **Logic-Free:** The UI may not perform engineering calculations (e.g., it cannot decide a wire's length; it must ask the Core).
* **Theme Driven:** All colors and sizes must be pulled from the semantic keys in `theme_tokens.json`.