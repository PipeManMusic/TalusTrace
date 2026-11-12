import sys
import os
import subprocess
import json
from pathlib import Path

# Configuration
TEST_DIR = "tests"

def run_tests():
    "Runs pytest and reports results. Returns True if passed."
    print("⌛ Running verification...")
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

# --- 1. Python Script Patching (New!) ---
def apply_python_script():
    script_file = "_patch_script.py"
    
    # Create a helpful template if it doesn't exist
    if not os.path.exists(script_file):
        template = """from pathlib import Path
import re
import os

# Helper: Read file
def read(path): 
    return Path(path).read_text(encoding='utf-8')

# Helper: Write file
def write(path, content): 
    Path(path).write_text(content, encoding='utf-8')
    print(f"✅ Updated {path}")

# --- Your Patch Logic Below ---
target_file = Path("talustrace/frontend/items_baseline.py")
"""
        with open(script_file, "w") as f:
            f.write(template)

    print("🔹 Opening Python Patch Script...")
    subprocess.call(["code", "--wait", script_file])

    print("🔹 Executing patch script...")
    try:
        # Execute the script in the same python environment
        result = subprocess.run([sys.executable, script_file], capture_output=False)
        
        if result.returncode == 0:
            print("✅ Script executed successfully.")
            run_tests()
        else:
            print("❌ Script execution failed.")
            
    except Exception as e:
        print(f"❌ Error running script: {e}")
    # We purposefully do NOT delete the script so you can re-run/fix it if it fails.

# --- 2. Git Apply Support (Robust) ---
def apply_git_apply():
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Error: 'git' command not found. Please install Git.")
        return

    temp_file = "_diff_input.patch"
    template = """--- a/example.py
+++ b/example.py
@@ -1,3 +1,3 @@
-print("Old")
+print("New")
"""
    with open(temp_file, 'w') as f:
        f.write(template)

    print("🔹 Opening Unified Diff input...")
    subprocess.call(["code", "--wait", temp_file])

    try:
        if os.path.getsize(temp_file) == len(template):
            print("⚠️ No diff provided (file unchanged).")
            return

        print("🔹 Applying patch with 'git apply'...")
        cmd = ["git", "apply", "--ignore-space-change", "--ignore-whitespace", "--unidiff-zero", temp_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Patch applied successfully.")
            run_tests()
        else:
            print("❌ Patch failed to apply.")
            print(f"   Error: {result.stderr.strip()}")
            
    except Exception as e:
        print(f"❌ Error executing git apply: {e}")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

# --- 3. Legacy JSON Support ---
def get_indent(line):
    # Strip newline so we don't count it as indentation
    clean = line.rstrip('\n\r')
    return clean[:len(clean) - len(clean.lstrip())]

def apply_patches_from_data(data, verify=True):
    patches = data.get("patches", []) if isinstance(data, dict) else data
    post_exec = data.get("exec") if isinstance(data, dict) else None
    
    file_groups = {}
    for p in patches:
        path = p.get('file')
        if not path: continue
        file_groups.setdefault(path, []).append(p)

    for filepath, group in file_groups.items():
        if not os.path.exists(filepath):
            print(f"🆕 Creating {filepath}")
            lines = []
        else:
            print(f"🔹 Patching {filepath}...")
            with open(filepath, 'r') as f: lines = f.readlines()

        group.sort(key=lambda x: int(x['start']), reverse=True)

        for patch in group:
            s, e = int(patch['start']), int(patch['end'])
            content = patch['content']
            if isinstance(content, str): content = [content]
            
            # Auto-indentation logic
            target_idx = max(0, s - 1)
            target_indent = get_indent(lines[target_idx]) if target_idx < len(lines) else ""
            patch_base_indent = get_indent(content[0]) if content else ""
            
            aligned_content = []
            for line in content:
                if not line.strip(): aligned_content.append('\n')
                else:
                    curr = get_indent(line)
                    rel = curr[len(patch_base_indent):]
                    new_line = target_indent + rel + line.lstrip()
                    if not new_line.endswith('\n'): new_line += '\n'
                    aligned_content.append(new_line)

            lines[max(0, s - 1):e] = aligned_content

        with open(filepath, 'w') as f: f.writelines(lines)

    print("✅ All patches applied.")
    if verify:
        if run_tests() and post_exec:
            subprocess.call(post_exec, shell=True)

def apply_json_interactive():
    temp_file = "_patch_input.json"
    template = {"patches": [{"file": "new_file.py", "start": 1, "end": 0, "content": ["print('hello')"]}], "exec": "ls"}
    with open(temp_file, 'w') as f: json.dump(template, f, indent=2)
    print("🔹 Opening Interactive JSON Patch...")
    subprocess.call(["code", "--wait", temp_file])
    try:
        with open(temp_file, 'r') as f: apply_patches_from_data(json.load(f))
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python dev.py --script # Write & Run a Python patch script")
        print("  python dev.py --diff   # Paste a Git Diff")
        print("  python dev.py --json   # Paste a JSON Patch")
        print("  python dev.py edit <file>")
    else:
        arg1 = sys.argv[1]
        if arg1 == "--script": apply_python_script()
        elif arg1 == "--diff": apply_git_apply()
        elif arg1 == "--json": apply_json_interactive()
        elif arg1 == "edit" and len(sys.argv) > 2: edit_file(sys.argv[2])