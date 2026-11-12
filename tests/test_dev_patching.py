import os
import sys
import pytest

# Add root to path so we can import dev
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dev import apply_patches_from_data

def test_indentation_preservation():
    """Verify that patching preserves indentation, especially after blank lines."""
    filename = "temp_test_indent_fix.py"
    content_initial = (
        "class MyClass:\n"
        "    def method(self):\n"
        "        pass\n"
        "        \n"
        "    def other(self):\n"
        "        pass\n"
    )
    with open(filename, 'w') as f:
        f.write(content_initial)

    patch = {
        "file": filename,
        "start": 4,
        "end": 4,
        "content": [
            "        # New Comment",
            "        print('Inserted')"
        ]
    }

    # Use verify=False to prevent infinite recursion
    apply_patches_from_data([patch], verify=False)

    with open(filename, 'r') as f:
        lines = f.readlines()

    if os.path.exists(filename):
        os.remove(filename)

    # Ensure correct relative indentation was applied
    assert lines[3].strip() == "# New Comment"
    assert lines[3].startswith("        ")
