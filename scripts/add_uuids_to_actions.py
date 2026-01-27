"""
Script to add UUIDs to actions.yaml for Talus Trace.
"""
import uuid
yaml_path = 'resources/config/actions.yaml'
output_path = 'resources/config/actions_with_uuids.yaml'
import yaml
with open(yaml_path, 'r') as f:
    data = yaml.safe_load(f)
for cmd in data['commands']:
    if 'uuid' not in cmd:
        cmd['uuid'] = str(uuid.uuid4())
with open(output_path, 'w') as f:
    yaml.dump(data, f, sort_keys=False)
print(f"UUIDs assigned and written to {output_path}")
