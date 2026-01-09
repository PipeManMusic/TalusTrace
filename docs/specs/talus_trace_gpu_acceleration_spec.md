# Talus Trace Specification: GPU Acceleration Architecture

**Status:** Draft for Phase 7  
**Philosophy:** 1. **Hybrid Execution:** Use the GPU for high-parallelism tasks (rendering, spatial queries, helix generation) while keeping business logic and state on the CPU.
2. **Viewport Optimization:** Direct the rendering pipeline to the hardware through OpenGL to achieve sub-millisecond frame times for complex harnesses.
3. **Graceful Fallback:** If GPU drivers are unavailable, the system must automatically revert to software rasterization and CPU-bound math.

---

## Part 1: Rendering Pipeline (The Viewport)

The `HarnessCanvas` must be upgraded from a standard `QWidget` viewport to an OpenGL-accelerated viewport.

### 1.1 Implementation: `QOpenGLWidget` Integration
* **Viewport:** The canvas will set a `QOpenGLWidget` as its viewport to leverage the hardware-accelerated `QPainter` engine.
* **Optimization Flags:**
    * `FullViewportUpdate`: Necessary for OpenGL to prevent CPU-side "dirty region" calculations.
    * `Antialiasing`: Enabled via `QPainter` hints, though specialized shaders may be used for high-quality wire smoothing.

---

## Part 2: Computational Acceleration (The Compute Layer)

Beyond pixels, the GPU will handle matrix-heavy engineering calculations defined in other specs (e.g., twisted pair geometry).

### 2.1 Helix Generation (Offloading `core/geometry.py`)
* **Current Bottleneck:** Generating 3D helix points for twisted pairs currently happens on the CPU and requires a binary cache.
* **GPU Fix:** Move the calculation into a Vertex Shader or Compute Shader.
    * **Input:** Send path nodes as a Uniform Array or Buffer Object.
    * **Execution:** The GPU calculates the sine/cosine offsets in parallel for all points in the segment.
    * **Result:** Real-time twisted pair rendering without the need for pre-generated binary blobs in `.cache/render/`.

### 2.2 Spatial Hashing (Offloading `core/spatial.py`)
* **Strategy:** Map the spatial grid to a GPU texture or buffer.
* **Audit Engine:** Parallelize Design Rule Checks (DRC) defined in `resources/rules/electrical.yaml` (e.g., measuring 10k clearances) using OpenGL Compute Shaders.

---

## Part 3: Data Management & Sync

### 3.1 Vertex Buffer Objects (VBOs)
* To achieve "Binary Speed," data should stay on the GPU as much as possible.
* The system will use VBOs to store wire paths, allowing the GPU to redraw them instantly during panning/zooming without re-sending coordinates from the CPU.

---

## Part 4: Implementation Roadmap

| Step | Task | Component |
| :--- | :--- | :--- |
| **1** | Enable `QOpenGLWidget` in `HarnessCanvas`. | UI / Viewport |
| **2** | Create `infra/gpu_manager.py` to handle shader compilation and context sharing. | Infrastructure |
| **3** | Refactor `TwistedPairItem` to use a Vertex Shader for helix geometry. | Tooling |
| **4** | Implement Compute Shader for "Always-On" DRC (Audit Engine). | Engineering |

---

## Part 5: Compliance Checklist
* **Binary Speed:** Is startup time under 100ms for 500+ wires?
* **Dumb Renderer:** Does the GPU stay limited to math/drawing while the Python Command Registry handles logic?
* **Fail Gracefully:** Does the `LayoutManager` catch OpenGL initialization errors and fall back to `QWidget`?