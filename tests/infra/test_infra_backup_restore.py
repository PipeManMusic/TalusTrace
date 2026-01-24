import pytest
from pathlib import Path
from infra.persistence import YAMLPersistence
from core.models import Harness
import time

def test_yaml_backup_and_restore(tmp_path):
    file_path = tmp_path / "backup_test.yaml"
    harness = Harness()
    harness.meta["name"] = "BackupTest"

    # Initial save
    YAMLPersistence.save(harness, file_path)
    assert file_path.exists()
    
    # Modify and save again to trigger backup
    harness.meta["name"] = "BackupTest2"
    time.sleep(1)  # Ensure timestamp difference
    YAMLPersistence.save(harness, file_path)

    # There should be at least one backup
    backups = YAMLPersistence.list_backups(file_path)
    assert len(backups) >= 1
    
    # Overwrite file with new data
    harness.meta["name"] = "BackupTest3"
    YAMLPersistence.save(harness, file_path)
    
    # All backups should contain 'BackupTest2'
    for backup in backups:
        YAMLPersistence.restore_backup(file_path, backup)
        restored = YAMLPersistence.load(file_path)
        assert restored.meta["name"] == "BackupTest2"

    # The current file should contain 'BackupTest3'
    harness.meta["name"] = "BackupTest3"
    YAMLPersistence.save(harness, file_path)
    restored3 = YAMLPersistence.load(file_path)
    assert restored3.meta["name"] == "BackupTest3"
