import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtGui import QImage


def test_demo_render_core_smaller_than_device(tmp_path):
    out = Path('artifacts') / 'demo_state_pad10.png'
    # Ensure fresh output
    if out.exists():
        out.unlink()

    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'

    # Render device mode and record dimensions
    subprocess.run([sys.executable, 'scripts/demo_render.py', '--mode', 'device', '--padding', '10'], check=True, env=env)
    img_device = QImage(str(out))
    w_device, h_device = img_device.width(), img_device.height()

    # Render core mode to same path (overwrites) and record dimensions
    subprocess.run([sys.executable, 'scripts/demo_render.py', '--mode', 'core', '--padding', '10'], check=True, env=env)
    img_core = QImage(str(out))
    w_core, h_core = img_core.width(), img_core.height()

    # Core render should be no taller than device render (may be equal if no pins present)
    assert h_core <= h_device
    # Widths should be the same (device width is the limiting horizontal union)
    assert w_core == w_device
