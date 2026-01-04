import os
import sys
from pathlib import Path


# Ensure the repository root is on sys.path so `talustrace` and `talus_trace` imports work.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Make Qt run headless during tests.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")