import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtGui import QImage


def test_demo_render_device_padding(tmp_path):
    out = Path('artifacts') / 'demo_state_pad10.png'
    # Ensure fresh output
    if out.exists():
        out.unlink()

    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'

    subprocess.run([sys.executable, 'scripts/demo_render.py', '--mode', 'device', '--padding', '10'], check=True, env=env)

    img = QImage(str(out))
    assert img.width() == 260
    # Pin visuals are drawn; device-mode height includes pin tips
    assert img.height() == 168
