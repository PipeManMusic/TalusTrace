# UI Test Isolation

All tests in this folder instantiate MainWindow or other full PySide6 UI components. These tests must be run in isolation from the rest of the suite to avoid segmentation faults due to PySide6/Qt resource cleanup issues.

## How to run UI tests safely

1. Run these tests in a separate process from the rest of the suite:

   ```sh
   pytest tests/ui
   ```

2. (Recommended for CI/headless) Use xvfb-run to provide a virtual display:

   ```sh
   xvfb-run -a pytest tests/ui
   ```

3. Do NOT run these tests in the same pytest invocation as non-UI tests.

## Why?
PySide6/Qt can crash (segfault) if QApplication and QGraphicsView/QGraphicsScene are created and destroyed repeatedly in the same process. Isolating these tests prevents resource conflicts and ensures reliable test results.
