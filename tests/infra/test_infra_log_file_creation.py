import os
import tempfile
from infra.logging import infra_log

def test_infra_log_creates_file():
    """
    Test that infra_log creates the log file at TALUSTRACE_LOG_PATH and writes a log entry.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "infra_test.log")
        os.environ["TALUSTRACE_INFRA_LOG"] = "1"
        os.environ["TALUSTRACE_LOG_PATH"] = log_path
        infra_log("Test log entry", level="info")
        assert os.path.exists(log_path), f"Log file was not created at {log_path}"
        with open(log_path, "r") as f:
            contents = f.read()
        assert "Test log entry" in contents, "Log entry not found in log file"
