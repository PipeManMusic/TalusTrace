# Talus Trace - Architecture & Roadmap

## Project Goal
A "Smart-Manual" CAD tool for designing automotive wiring harnesses, focusing on fabrication speed and 1:1 formboard printing.

## 🧠 Core Philosophy
1.  **Constraint-Based Drafting:** The software handles the straight lines and snapping; the human handles the routing.
2.  **Local-First:** All data is stored in human-readable YAML files.
3.  **Physical-First:** The end goal is a physical label and a physical crimp, not just a pretty picture.

## 🏗 System Architecture

### 1. Data Layer (The Source of Truth)
* **Format:** YAML (`data/*.yaml`).
* **Validation:** Pydantic V2 Models (`backend/models.py`).
* **Why Pydantic?** It ensures that every loaded harness strictly adheres to the schema before the GUI touches it.

### 2. The Backend ("The Math")
* **Router (`backend/router.py`):** Calculates wire paths using the "Rubber Band" logic (Elbows).
* **Auto-Sizer (`backend/sizer.py`):** Calculates the dimensions of Device Boxes based on pin counts and labels.
* **Label Manager (`backend/labels.py`):** The "Typing Copilot" that generates short-codes (e.g., `CLNT_TMP`).

### 3. The Frontend ("The Canvas")
* **Framework:** PySide6 (Qt for Python).
* **Canvas (`frontend/canvas.py`):** A specialized `QGraphicsScene` with:
    * **Infinite Grid:** 20px Snap.
    * **Layered Rendering:** Background (Halo) -> Middle (Stripe) -> Foreground (Color).
* **Interaction:** Double-click to add elbows; Drag to snap orthogonal. Note: Twisted-pair bundles do not create an implicit main handle — elbows are explicit only (user-added).

## 🛠 Developer Workflow: The "Full-Overwrite" Protocol
To eliminate merge conflicts and logic drift, we utilize a strict **Full-File Overwrite Strategy**.

### The Process
1.  **Trigger Edit:** User asks AI to "Update `frontend/canvas.py` to add Grid Snapping."
2.  **Generation:** AI generates the **Complete File Content**.
3.  **Overwrite:** User pastes the content into the file.
4.  **Verification:** User runs `python dev.py test` to verify the new feature.

## 📂 Directory Structure
```text
TalusTrace/
├── data/                  # YAML Projects
├── talustrace/
│   ├── backend/
│   │   ├── models.py      # Pydantic Schemas
│   │   └── printer.py     # Brother PT-P700 Logic
│   └── frontend/
│       ├── canvas.py      # The Drawing Board
│       └── items.py       # Wire & Device Graphics
├── tests/
│   ├── test_models.py     # Verify YAML Parsing
│   ├── test_geometry.py   # Verify Orthogonal Snapping
│   └── test_gui.py        # Verify Canvas Interaction
└── dev.py                 # Automation Script