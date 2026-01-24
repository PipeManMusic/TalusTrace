import os
import tempfile
import pytest
from infra.context import Context
from api import actions

class DummyHarness:
    def __init__(self, name):
        self.meta = {'name': name}
    def to_dict(self):
        return {'meta': self.meta}
    @classmethod
    def from_dict(cls, d):
        return cls(d['meta']['name'])

def test_json_import_export(tmp_path, monkeypatch):
    # Patch Harness for test
    monkeypatch.setattr('infra.persistence.Harness', DummyHarness)
    project = DummyHarness('json-test')
    json_path = tmp_path / 'project.json'
    # Export
    actions.export_project(project, json_path)
    assert json_path.exists()
    # Import
    loaded = actions.import_project(json_path)
    assert isinstance(loaded, DummyHarness)
    assert loaded.meta['name'] == 'json-test'

def test_yaml_import_export(tmp_path, monkeypatch):
    # Patch Harness for test
    monkeypatch.setattr('infra.persistence.Harness', DummyHarness)
    project = DummyHarness('yaml-test')
    yaml_path = tmp_path / 'project.yaml'
    # Export
    actions.export_project(project, yaml_path)
    assert yaml_path.exists()
    # Import
    loaded = actions.import_project(yaml_path)
    assert isinstance(loaded, DummyHarness)
    assert loaded.meta['name'] == 'yaml-test'
