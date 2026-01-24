"""
Importers: Import Other Project Formats
--------------------------------------

Usage:
    from infra.importers import import_from_csv, import_from_legacy_json
    harness = import_from_csv('file.csv')
    harness = import_from_legacy_json('file.json')

- Extend with new importers as needed (e.g., XML, EDA, etc).

Maintenance:
    - Add new importers for each supported format.
    - For advanced use, add format detection and unified import API.
"""
import csv
import json
from core.models import Harness

# Example: Import from CSV (assumes flat wire list for demo)
def import_from_csv(file_path):
    """Import a project from a CSV file (simple demo: wires only)."""
    with open(file_path) as f:
        reader = csv.DictReader(f)
        wires = list(reader)
    # For demo, create a Harness with wires as meta
    h = Harness()
    h.meta['imported_wires'] = wires
    return h

# Example: Import from legacy JSON
def import_from_legacy_json(file_path):
    """Import a project from a legacy JSON file (assumes dict structure)."""
    with open(file_path) as f:
        data = json.load(f)
    h = Harness.from_dict(data)
    return h
