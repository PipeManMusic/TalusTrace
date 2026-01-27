"""
Script to add UUIDs to i18n YAML files for Talus Trace actions.
"""
import yaml
import sys

actions_path = 'resources/config/actions_with_uuids.yaml'
i18n_path = 'resources/config/langs/en.yaml'
output_path = 'resources/config/langs/en_with_uuids.yaml'

with open(actions_path, 'r') as f:
    actions = yaml.safe_load(f)['commands']
with open(i18n_path, 'r') as f:
    i18n = yaml.safe_load(f)

# Build a mapping from action id to uuid
id_to_uuid = {a['id']: a['uuid'] for a in actions if 'uuid' in a}

# List of (id, label) pairs to migrate (from old i18n keys)
label_map = {
    'tool.add_generic_device': 'Add Generic Device',
    'tool.select': 'Select Mode',
    'tool.move': 'Move',
    'tool.wire': 'Draw Wire',
    'tool.measure': 'Measure',
    'device.create_wizard': 'Device Wizard',
    'edit.rotate_cw': 'Rotate 90°',
    'edit.rotate_ccw': 'Rotate -90°',
    'edit.delete': 'Delete',
    'edit.undo': 'Undo',
    'edit.redo': 'Redo',
    'view.zoom_extents': 'Zoom Extents',
    'view.zoom_selected': 'Zoom Selected',
    'view.toggle_grid': 'Toggle Grid',
    'view.toggle_property_panel': 'Properties',
    'view.toggle_project_browser': 'Project Browser',
    'view.toggle_library': 'Component Library',
    'view.reset_layout': 'Reset Layout',
    'file.new': 'New',
    'file.open': 'Open',
    'file.save': 'Save',
    'file.exit': 'Exit',
    'file.export_bom': 'Export BOM',
    'file.export_wirelist': 'Export Wires',
}

# Add UUID-based keys to i18n
i18n_out = dict(i18n)
for action_id, label in label_map.items():
    uuid = id_to_uuid.get(action_id)
    if uuid:
        i18n_out[uuid] = label

with open(output_path, 'w') as f:
    yaml.dump(i18n_out, f, sort_keys=False)
print(f"UUID-based i18n keys written to {output_path}")
