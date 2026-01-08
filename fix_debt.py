import os
import re

# Refactoring Rules
replacements = [
    # 1. Class Renaming (Connector -> Device)
    (r'from core\.device import Connector', 'from core.device import Device'),
    (r'Connector\(', 'Device('),
    
    # 2. Wire Field Standard (source_pin_id -> from_conn)
    (r'from_conn=', 'from_conn='),
    (r'to_conn=', 'to_conn='),
    (r'\.from_conn', '.from_conn'),
    (r'\.to_conn', '.to_conn'),
    
    # 3. Geometry Standard (route -> path_nodes)
    (r'path_nodes=', 'path_nodes='),
    (r'\.path_nodes', '.path_nodes'),
    
    # 4. Harness Locking (mark_saved -> increment_revision)
    (r'\.mark_saved\(\)', '.increment_revision()'),
    
    # 5. API Netlist Import Fixes (Specific variable mapping)
    (r'from_conn=source_pin', 'from_conn=source_pin'), # Fix potential loop
    (r'from_conn=source_pin', 'from_conn=source_pin'),
    (r'to_conn=target_pin', 'to_conn=target_pin'),
]

def patch_file(path):
    with open(path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Apply regex replacements
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content)
        
    # Manual Fix: Device Position Assertion (List -> Float)
    if "assert device.pos ==" in content:
        content = content.replace(
            "assert device.x == 100.0
    assert device.y == 250.0", 
            "assert device.x == 100.0\n    assert device.y == 250.0"
        )
        # Handle the failure case in test_infra_transactions
        content = content.replace(
            "assert device.x == 0.0
    assert device.y == 0.0",
            "assert device.x == 0.0\n    assert device.y == 0.0"
        )

    if content != original:
        print(f"Fixed: {path}")
        with open(path, 'w') as f:
            f.write(content)

# Walk directory
print("Starting Phase 6 Debt Cleanup...")
for root, dirs, files in os.walk("."):
    if "venv" in root or ".git" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            patch_file(os.path.join(root, file))
            
print("Cleanup Complete.")