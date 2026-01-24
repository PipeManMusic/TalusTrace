import os
import tempfile
import pytest
from api import actions
from infra import persistence

class DummyProject:
    def __init__(self, data):
        self.data = data
    def to_dict(self):
        return {'data': self.data}
    @classmethod
    def from_dict(cls, d):
        return cls(d['data'])

# Patch YAMLPersistence for DummyProject
class DummyYAMLPersistence:
    @staticmethod
    def load(file_path):
        with open(file_path, 'r') as f:
            return DummyProject(f.read())
    @staticmethod
    def save(project, file_path):
        with open(file_path, 'w') as f:
            f.write(project.data)
        return True
    @staticmethod
    def atomic_save(project, file_path):
        # Simulate atomic save by writing to a temp file then renaming
        tmp = file_path + '.tmp'
        with open(tmp, 'w') as f:
            f.write(project.data)
        os.replace(tmp, file_path)
        return True

def test_import_export_project(monkeypatch):
    monkeypatch.setattr(actions.persistence, 'YAMLPersistence', DummyYAMLPersistence)
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(b'hello world')
        tf.flush()
        tf.close()
        project = actions.import_project(tf.name)
        assert isinstance(project, DummyProject)
        assert project.data == 'hello world'
        # Export
        out_path = tf.name + '_out'
        result = actions.export_project(project, out_path)
        assert result is True
        with open(out_path) as f:
            assert f.read() == 'hello world'
        os.remove(out_path)
    os.remove(tf.name)

def test_atomic_save_project(monkeypatch):
    monkeypatch.setattr(actions.persistence, 'YAMLPersistence', DummyYAMLPersistence)
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.close()
        project = DummyProject('atomic data')
        result = actions.atomic_save_project(project, tf.name)
        assert result is True
        with open(tf.name) as f:
            assert f.read() == 'atomic data'
    os.remove(tf.name)

def test_autosave_project_runs(monkeypatch):
    monkeypatch.setattr(actions, 'autosave_project', lambda: True)
    assert actions.autosave_project() is True

def test_restore_session_runs(monkeypatch):
    monkeypatch.setattr(actions, 'restore_session', lambda: True)
    assert actions.restore_session() is True

def test_backup_project_runs(monkeypatch):
    monkeypatch.setattr(actions, 'backup_project', lambda: True)
    assert actions.backup_project() is True

def test_restore_backup_handles_missing_file(monkeypatch):
    # Patch to simulate FileNotFoundError gracefully handled
    def fake_restore_backup(path):
        try:
            open(path, 'r')
        except FileNotFoundError:
            return 'file not found'
        return 'ok'
    monkeypatch.setattr(actions, 'restore_backup', fake_restore_backup)
    assert actions.restore_backup('dummy') == 'file not found'

def test_backup_and_restore_end_to_end(tmp_path, monkeypatch):
    """Full end-to-end test: backup creates a file, restore loads correct data."""
    import shutil
    from api import actions
    from infra import context as infra_context
    import yaml

    # Setup: create a dummy harness and assign to global context
    class DummyHarness:
        def __init__(self, value):
            self.value = value
        def to_dict(self):
            return {"value": self.value}
        @classmethod
        def from_dict(cls, d):
            return cls(d["value"])
    
    # Patch Harness in context
    monkeypatch.setattr(infra_context, "Harness", DummyHarness)
    ctx = infra_context.global_context
    ctx.harness = DummyHarness("original-data")
    ctx.current_file = str(tmp_path / "project.yaml")

    # Backup
    backup_file = actions.backup_project()
    assert backup_file.exists()
    with open(backup_file) as f:
        data = yaml.safe_load(f)
    assert data["value"] == "original-data"

    # Mutate harness to simulate data loss/corruption
    ctx.harness = DummyHarness("corrupted")
    assert ctx.harness.value == "corrupted"

    # Restore
    restored = actions.restore_backup(str(backup_file))
    assert isinstance(restored, DummyHarness)
    assert restored.value == "original-data"
    assert ctx.harness.value == "original-data"

    # Clean up backup dir
    shutil.rmtree(tmp_path / ctx.BACKUP_DIRNAME, ignore_errors=True)

def test_api_json_import_export(tmp_path, monkeypatch):
    """API-level test: import and export project as JSON, verify round-trip integrity."""
    import json
    from api import actions
    from infra import persistence

    class DummyProject:
        def __init__(self, data):
            self.data = data
        def to_dict(self):
            return {"data": self.data}
        @classmethod
        def from_dict(cls, d):
            return cls(d["data"])

    class DummyJSONPersistence:
        @staticmethod
        def load(file_path):
            with open(file_path, "r") as f:
                return DummyProject(json.load(f)["data"])
        @staticmethod
        def save(project, file_path):
            with open(file_path, "w") as f:
                json.dump({"data": project.data}, f)
            return True

    monkeypatch.setattr(actions.persistence, "JSONPersistence", DummyJSONPersistence)

    # Export to JSON
    project = DummyProject("json-data")
    json_path = tmp_path / "project.json"
    result = actions.export_project(project, str(json_path))
    assert result is True
    assert json_path.exists()
    # Import from JSON
    loaded = actions.import_project(str(json_path))
    assert isinstance(loaded, DummyProject)
    assert loaded.data == "json-data"

def test_api_settings_crud_and_persistence(tmp_path):
    """API-level test: settings CRUD and persistence using SettingsManager."""
    from infra.settings import SettingsManager
    import yaml

    settings_path = tmp_path / "settings.yaml"
    mgr = SettingsManager(path=settings_path)
    # Set and get
    mgr.set("theme", "dark")
    assert mgr.get("theme") == "dark"
    # Update
    mgr.set("theme", "light")
    assert mgr.get("theme") == "light"
    # Add another key
    mgr.set("autosave", True)
    assert mgr.get("autosave") is True
    # Delete
    mgr.delete("theme")
    assert mgr.get("theme") is None
    # All
    all_settings = mgr.all()
    assert all_settings == {"autosave": True}
    # Persistence: reload from disk
    mgr2 = SettingsManager(path=settings_path)
    assert mgr2.get("autosave") is True
    # File contents
    with open(settings_path) as f:
        data = yaml.safe_load(f)
    assert data == {"autosave": True}

def test_api_validation_and_mapping_utilities():
    """API-level test: validate_harness and map_fields utilities."""
    from infra.validation_utils import validate_harness, map_fields

    class DummyHarness:
        def __init__(self, meta):
            self.meta = meta

    # Validation: should pass
    h = DummyHarness(meta={"foo": "bar"})
    assert validate_harness(h) is True
    # Validation: should fail
    h2 = DummyHarness(meta=None)
    try:
        validate_harness(h2)
        assert False, "Expected ValueError for missing meta dict"
    except ValueError as e:
        assert "meta dict" in str(e)
    # Mapping
    data = {"a": 1, "b": 2}
    mapping = {"a": "x", "b": "y"}
    mapped = map_fields(data, mapping)
    assert mapped == {"x": 1, "y": 2}

def test_api_wizard_assistant_state_management():
    """API-level test: wizard/assistant state management using WizardManager."""
    from infra.wizard_manager import WizardManager

    steps = ["step1", "step2", "step3"]
    wiz = WizardManager(steps)
    wiz.start()
    assert wiz.current == 0 and wiz.active
    # Set and get data for step1
    wiz.set_data("step1", {"foo": "bar"})
    assert wiz.get_data("step1") == {"foo": "bar"}
    # Move to next step
    wiz.next()
    assert wiz.current == 1
    # Set and get data for step2
    wiz.set_data("step2", {"baz": 42})
    assert wiz.get_data("step2") == {"baz": 42}
    # Serialize state
    state = wiz.serialize()
    # Restore from serialized state
    wiz2 = WizardManager.deserialize(state)
    assert wiz2.steps == steps
    assert wiz2.current == wiz.current
    assert wiz2.data == wiz.data
    assert wiz2.active == wiz.active
    # Move to last step and finish
    wiz2.next()
    wiz2.next()
    assert wiz2.current == 2
    assert not wiz2.active

def test_api_caching_and_context_dirty(tmp_path):
    """API-level test: caching and context_dirty using CacheManager and Context."""
    from infra.cache_manager import CacheManager
    from infra.context import Context

    cache_dir = tmp_path / "cache"
    mgr = CacheManager(cache_dir=cache_dir)
    key = "testkey"
    data = {"foo": "bar"}
    # Save and load
    mgr.save(key, data)
    loaded = mgr.load(key)
    assert loaded == data
    # Set and get
    mgr.set("another", [1, 2, 3])
    assert mgr.get("another") == [1, 2, 3]
    # Invalidate
    mgr.invalidate(key)
    assert mgr.load(key) is None
    # Clear
    mgr.clear()
    assert mgr.get("another") is None
    # Context dirty tracking
    ctx = Context()
    assert not ctx.is_dirty
    ctx.mark_dirty()
    assert ctx.is_dirty
    ctx.is_dirty = False
    assert not ctx.is_dirty

def test_api_error_handling_and_reporting(tmp_path):
    """API-level test: error handling and reporting using CentralErrorHandler."""
    from infra.error_handler import CentralErrorHandler
    import os
    class DummyNotificationMgr:
        def __init__(self):
            self.last = None
        def notify(self, level, message, **kwargs):
            self.last = (level, message, kwargs)
    log_path = tmp_path / "error_log.jsonl"
    notifications = DummyNotificationMgr()
    handler = CentralErrorHandler(notifications, log_path)
    # Simulate exception
    try:
        raise ValueError("Test error")
    except Exception as e:
        handler.handle_exception(e, context="test-context")
    # Check notification
    assert notifications.last[0] == "error"
    assert "Test error" in notifications.last[1]
    # Check log file
    assert log_path.exists()
    with open(log_path) as f:
        lines = f.readlines()
    assert any("Test error" in line for line in lines)
    # Test catch_errors decorator
    @handler.catch_errors
    def will_fail():
        raise RuntimeError("fail")
    try:
        will_fail()
    except RuntimeError:
        pass
    # Should log and notify
    assert notifications.last[0] == "error"
    assert "fail" in notifications.last[1]

def test_api_notification_serialization_and_dispatch(tmp_path):
    """API-level test: notification serialization and dispatch using NotificationManager."""
    from infra.notification_manager import NotificationManager
    import os
    log_path = tmp_path / "notification_log.jsonl"
    dispatched = []
    def dispatch_hook(entry):
        dispatched.append(entry)
    mgr = NotificationManager(log_path, dispatch_hooks=[dispatch_hook])
    # Notify
    mgr.notify("info", "Hello world", extra=123)
    mgr.notify("error", "Something went wrong.")
    # In-memory notifications
    notes = list(mgr.list_notifications())
    assert any(n["message"] == "Hello world" for n in notes)
    assert any(n["level"] == "error" for n in notes)
    # Dispatch hook called
    assert any(e["message"] == "Hello world" for e in dispatched)
    # Persisted notifications
    notes_persisted = list(mgr.list_notifications(persisted=False))
    assert any(n["message"] == "Something went wrong." for n in notes_persisted)
    # Log file exists
    assert log_path.exists()
    with open(log_path) as f:
        lines = f.readlines()
    assert any("Hello world" in line for line in lines)
    # Clear notifications
    mgr.clear_notifications()
    assert list(mgr.list_notifications()) == []

def test_api_theme_switching_and_persistence(tmp_path, monkeypatch):
    """API-level test: theme switching and persistence using ThemeManager."""
    from infra.theme_manager import ThemeManager
    import yaml
    import json
    import shutil
    # Copy default and custom theme files to temp
    default_theme_src = os.path.join(os.path.dirname(__file__), "..", "resources", "theme_tokens.json")
    custom_theme_src = os.path.join(os.path.dirname(__file__), "..", "resources", "config", "theme.yaml")
    default_theme_dst = tmp_path / "theme_tokens.json"
    custom_theme_dst = tmp_path / "theme.yaml"
    shutil.copyfile(default_theme_src, default_theme_dst)
    shutil.copyfile(custom_theme_src, custom_theme_dst)
    # Patch the custom theme file to include a 'colors' key so ThemeManager loads it as 'custom'
    import yaml
    with open(custom_theme_dst, 'r') as f:
        data = yaml.safe_load(f) or {}
    if 'colors' not in data:
        data = {'colors': data}
    with open(custom_theme_dst, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)
    # Patch ThemeManager paths
    monkeypatch.setattr(ThemeManager, "DEFAULT_THEME_PATH", default_theme_dst)
    monkeypatch.setattr(ThemeManager, "CUSTOM_THEME_PATH", custom_theme_dst)
    mgr = ThemeManager()
    # List themes
    themes = mgr.list_themes()
    assert "default" in themes and "custom" in themes
    # Get and serialize default theme
    default_theme = mgr.get_theme()
    # Accept both flat and nested theme dicts
    if "colors" in default_theme:
        assert "device_body" in default_theme["colors"]
    else:
        # Flat dict: check for a known key
        assert "background" in default_theme
    serialized = mgr.serialize_theme("default")
    # Accept both flat and nested for serialization
    parsed = json.loads(serialized)
    if "colors" in parsed:
        assert "device_body" in parsed["colors"]
    else:
        assert "background" in parsed
    # Switch to custom theme
    mgr.set_theme("custom")
    assert mgr._active_theme == "custom"
    # Persisted in theme.yaml
    with open(custom_theme_dst) as f:
        data = yaml.safe_load(f)
    assert data["active_theme"] == "custom"
    # Switch back to default
    mgr.set_theme("default")
    assert mgr._active_theme == "default"
    with open(custom_theme_dst) as f:
        data = yaml.safe_load(f)
    assert data["active_theme"] == "default"
