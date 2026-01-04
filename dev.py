import sys
import os
import subprocess
import json

# Configuration
TEST_DIR = "tests"

def run_tests():
    """Runs pytest and reports results. Returns True if passed."""
    print("⌛ File closed. Running verification...")
    print("⚡ Verifying...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    result = subprocess.run(["pytest", TEST_DIR], capture_output=False, env=env)
    if result.returncode == 0:
        print("✅ VERIFIED: Changes passed tests.")
        return True
    else:
        print("❌ FAILED: Changes broke the build.")
        return False

def edit_file(filepath):
    print(f"🔹 VS Code detected. Opening {filepath}...")
    subprocess.call(["code", "--wait", filepath])
    run_tests()

def get_indent(line):
    return line[:len(line) - len(line.lstrip())]

def apply_patches_from_data(data):
    patches = []
    post_exec = None
    if isinstance(data, list):
        patches = data
    elif isinstance(data, dict):
        patches = data.get("patches", [])
        post_exec = data.get("exec")
    
    file_groups = {}
    for p in patches:
        path = p.get('file')
        if not path: continue
        if path not in file_groups:
            file_groups[path] = []
        file_groups[path].append(p)

    for filepath, group in file_groups.items():
        # NEW: Ensure directory exists
        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)

        # NEW: If file doesn't exist, start with an empty list
        if not os.path.exists(filepath):
            print(f"🆕 Creating new file: {filepath}")
            lines = []
        else:
            print(f"🔹 Patching {filepath}...")
            with open(filepath, 'r') as f:
                lines = f.readlines()

        group.sort(key=lambda x: int(x['start']), reverse=True)

        for patch in group:
            s = int(patch['start'])
            e = int(patch['end'])
            content = patch['content']
            if isinstance(content, str): content = [content]
            
            target_idx = max(0, s - 1)
            target_indent = get_indent(lines[target_idx]) if target_idx < len(lines) else ""
            patch_base_indent = get_indent(content[0]) if content else ""
            
            aligned_content = []
            for line in content:
                stripped = line.lstrip()
                if not stripped:
                    aligned_content.append('\n')
                else:
                    current_indent = get_indent(line)
                    relative_indent = current_indent[len(patch_base_indent):]
                    new_line = target_indent + relative_indent + stripped
                    if not new_line.endswith('\n'): new_line += '\n'
                    aligned_content.append(new_line)

            idx_start = max(0, s - 1)
            idx_end = e 
            lines[idx_start:idx_end] = aligned_content

        with open(filepath, 'w') as f:
            f.writelines(lines)

    print("✅ All patches applied.")
    if run_tests():
        if post_exec:
            print(f"\n🚀 Tests Passed. Executing: {post_exec}\n")
            subprocess.call(post_exec, shell=True)

def apply_json_interactive():
    temp_file = "_patch_input.json"
    template = {"patches": [{"file": "new_file.py", "start": 1, "end": 0, "content": ["print('hello')"]}], "exec": "ls"}
    with open(temp_file, 'w') as f:
        json.dump(template, f, indent=2)
    print("🔹 Opening Interactive JSON Patch...")
    subprocess.call(["code", "--wait", temp_file])
    try:
        with open(temp_file, 'r') as f:
            data = json.load(f)
        apply_patches_from_data(data)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON provided: {e}")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

if __name__ == "__main__":
    if len(sys.argv) < 2: pass
    else:
        arg1 = sys.argv[1]
        if arg1 == "--json": apply_json_interactive()
        elif arg1 == "edit" and len(sys.argv) > 2: edit_file(sys.argv[2])