import pytest
from infra.settings import SettingsManager

def test_settings_manager_crud(tmp_path):
    path = tmp_path / "settings.yaml"
    mgr = SettingsManager(path)
    # Initially empty
    assert mgr.all() == {}
    # Set and get
    mgr.set("theme", "dark")
    assert mgr.get("theme") == "dark"
    # Update
    mgr.set("theme", "light")
    assert mgr.get("theme") == "light"
    # Add another
    mgr.set("fontsize", 14)
    assert mgr.get("fontsize") == 14
    # Delete
    mgr.delete("theme")
    assert mgr.get("theme") is None
    # Persistence
    mgr2 = SettingsManager(path)
    assert mgr2.get("fontsize") == 14
    assert mgr2.get("theme") is None
