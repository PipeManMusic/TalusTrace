import pytest
from infra.importers import import_from_csv, import_from_legacy_json
import json
import csv
from core.models import Harness

def test_import_from_csv(tmp_path):
    file_path = tmp_path / 'test.csv'
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name'])
        writer.writeheader()
        writer.writerow({'id': '1', 'name': 'WireA'})
        writer.writerow({'id': '2', 'name': 'WireB'})
    h = import_from_csv(file_path)
    assert isinstance(h, Harness)
    assert len(h.meta['imported_wires']) == 2
    assert h.meta['imported_wires'][0]['name'] == 'WireA'

def test_import_from_legacy_json(tmp_path):
    file_path = tmp_path / 'test.json'
    data = {'meta': {'foo': 'bar'}}
    with open(file_path, 'w') as f:
        json.dump(data, f)
    h = import_from_legacy_json(file_path)
    assert isinstance(h, Harness)
    assert h.meta['foo'] == 'bar'
