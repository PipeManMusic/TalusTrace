import os
import subprocess
import time
import pytest

def test_qt_warning_logging():
    log_path = os.path.expanduser('~/talustrace_app.log')
    # Remove log if it exists
    if os.path.exists(log_path):
        os.remove(log_path)
    # Run the app for a short time
    proc = subprocess.Popen(['python3', '-m', 'ui.app'])
    time.sleep(2)  # Give it time to start and emit warnings
    proc.terminate()
    proc.wait()
    # Check if log file was created and contains known Qt warning text
    assert os.path.exists(log_path), 'Log file was not created.'
    with open(log_path, 'r') as f:
        log_content = f.read()
    assert 'qt.qpa.wayland' in log_content or 'Failed to create grabbing popup' in log_content, 'Qt/system warnings not found in log.'
