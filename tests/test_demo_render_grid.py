import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtGui import QImage


def test_demo_render_grid_pixel(tmp_path):
    out = Path('artifacts') / 'demo_state_pad10.png'
    # Ensure fresh output
    if out.exists():
        out.unlink()

    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'

    subprocess.run([sys.executable, 'scripts/demo_render.py', '--mode', 'device', '--padding', '10'], check=True, env=env)

    img = QImage(str(out))
    # Sample a small neighborhood around a pixel that should fall on a grid line near the top-left
    cx, cy = 10, 10
    found_nonwhite = False
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = cx + dx, cy + dy
            if x < 0 or y < 0 or x >= img.width() or y >= img.height():
                continue
            px = img.pixel(x, y)
            if px != 0xffffffff:
                found_nonwhite = True
                break
        if found_nonwhite:
            break
    assert found_nonwhite, "Expected at least one non-white pixel in the sampled neighborhood indicating a grid line"
