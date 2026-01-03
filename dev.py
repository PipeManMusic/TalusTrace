#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil

# CONFIGURATION: Talus Trace Test Map
TEST_MAP = {
    # Backend Logic (The Math)
    "talustrace/backend/models.py": "tests/test_models.py",
    "talustrace/backend/router.py": "tests/test_geometry.py",
    "talustrace/backend/sizer.py": "tests/test_sizer.py",
    "talustrace/backend/labels.py": "tests/test_labels.py",

    # Frontend (The Canvas)
    "talustrace/frontend/canvas.py": "tests/test_gui.py",
    "talustrace/frontend/app.py": "tests/test_gui.py",
    "talustrace/frontend/items.py": "tests/test_rendering.py",

    # Test Files (Self-Verification)
    "tests/test_models.py": "tests/test_models.py",
    "tests/test_geometry.py": "tests/test_geometry.py",
    "tests/test_gui.py": "tests/test_gui.py",
}

def run_tests(target_file):
    """Runs the specific test suite associated with the edited file."""
    print(f"⚡ Verifying {target_file}...")
    
    # Default to running ALL tests if mapping not found
    test_target = TEST_MAP.get(target_file, ".")
    
    # --- FIX: Add current directory to PYTHONPATH ---
    env = os.environ.copy()
    # Adds the current folder to the path so 'talustrace' module is found
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    
    # Run pytest with color output enabled using the modified env
    result = subprocess.run(
        ["pytest", test_target, "-v"], 
        capture_output=False, 
        env=env
    )
    
    if result.returncode == 0:
        print(f"✅ VERIFIED: Changes to {target_file} passed tests.")
    else:
        print(f"❌ FAILED: Changes to {target_file} broke the build.")

def get_editor_command(filename):
    """Determines the best editor to use (VS Code > Editor Env > Nano)."""
    env_editor = os.getenv('EDITOR')
    if env_editor:
        return [env_editor, filename]
    
    if shutil.which('code'):
        print("🔹 VS Code detected. Opening in 'Wait' mode...")
        return ['code', '--wait', filename]
    
    print("🔸 VS Code not found. Falling back to nano.")
    return ['nano', filename]

def edit_file(filename):
    """Opens the file, waits for user to paste content, then runs tests."""
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            pass

    cmd = get_editor_command(filename)
    print(f"📝 Opening {filename}...")
    print("👉 ACTION: Select All -> Paste New Code -> Save -> Close Tab.")
    
    subprocess.call(cmd)
    
    print("⌛ File closed. Running verification...")
    run_tests(filename)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 dev.py [edit|test] [filename]")
        return
        
    command = sys.argv[1]
    target = sys.argv[2]
    
    if command == "edit":
        edit_file(target)
    elif command == "test":
        run_tests(target)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()