
import ast
import os
import pytest

UI_FUNCTIONS = [
    'setWindowTitle', 'QLabel', 'QPushButton', 'QAction', 'addMenu', 'setHeaderLabel', 'addRow', 'setText', 'setToolTip'
]

@pytest.mark.parametrize("filename", [
    "ui/app.py",
    "ui/main_window.py",
    "ui/layout_manager.py",
])
def test_no_hardcoded_ui_strings(filename):
    """Fail if hardcoded UI strings are used instead of I18N.get."""
    path = os.path.join(os.path.dirname(__file__), "..", filename)
    with open(path, "r") as f:
        source = f.read()
    tree = ast.parse(source, filename)
    for node in ast.walk(tree):
        # Only check calls to known UI string functions
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in UI_FUNCTIONS:
                for arg in node.args:
                    # Only fail if argument is a string constant and not wrapped in I18N.get
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        # Check if parent is a call to I18N.get
                        if not (isinstance(arg, ast.Call) and getattr(arg.func, 'attr', None) == 'get'):
                            pytest.fail(f"Hardcoded UI string '{arg.value}' in {filename} for {node.func.attr}. Use I18N.get().")
