Running tests locally

- Create and activate a virtual environment (recommended):

  python3 -m venv venv
  source venv/bin/activate

- Install project dependencies (requirements.txt already includes PySide6 & pytest):

  pip install -r requirements.txt

- Run tests with headless Qt (recommended):

  QT_QPA_PLATFORM=offscreen pytest -q

Notes
- On systems where `offscreen` is not available, you can use an X virtual framebuffer (Xvfb) or adjust `QT_QPA_PLATFORM` appropriately.
- CI runs tests on GitHub Actions and sets `QT_QPA_PLATFORM=offscreen` to allow headless execution.
