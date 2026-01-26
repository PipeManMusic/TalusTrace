import yaml

actions_path = 'resources/config/actions_with_uuids.yaml'
ui_layout_path = 'resources/config/ui_layout.yaml'
output_path = 'resources/config/ui_layout_with_uuids.yaml'

with open(actions_path, 'r') as f:
    actions = yaml.safe_load(f)['commands']
with open(ui_layout_path, 'r') as f:
    ui_layout = yaml.safe_load(f)

# Build a mapping from action id to uuid
id_to_uuid = {a['id']: a['uuid'] for a in actions if 'uuid' in a}

def replace_command_with_uuid(item):
    if isinstance(item, dict):
        if 'command' in item and item['command'] in id_to_uuid:
            item['uuid'] = id_to_uuid[item['command']]
            del item['command']
        for k, v in item.items():
            replace_command_with_uuid(v)
    elif isinstance(item, list):
        for v in item:
            replace_command_with_uuid(v)

replace_command_with_uuid(ui_layout)

with open(output_path, 'w') as f:
    yaml.dump(ui_layout, f, sort_keys=False)
print(f"UUIDs substituted in {output_path}")
