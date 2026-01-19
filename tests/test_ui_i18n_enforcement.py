import ast
import os
import pytest

UI_PATHS = [
    'ui/',
    'ui/dialogs/',
    'ui/panels/',
]

I18N_IMPORT = 'I18N.get'

@pytest.mark.parametrize('folder', UI_PATHS)
def test_no_hardcoded_strings_in_ui(folder):
    # Only check .py files
    for fname in os.listdir(folder):
        if not fname.endswith('.py'):
            continue
        path = os.path.join(folder, fname)
        with open(path, 'r') as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            # Look for string literals in setWindowTitle, QLabel, QPushButton, QAction, addMenu, setHeaderLabel, addRow, etc.
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    if func.attr in [
                        'setWindowTitle', 'QLabel', 'QPushButton', 'QAction', 'addMenu', 'setHeaderLabel', 'addRow'
                    ]:
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                # Only allow if argument is from I18N.get
                                parent = getattr(node, 'parent', None)
                                if not (isinstance(arg.s, str) and I18N_IMPORT in ast.unparse(node)):
                                    pytest.fail(f"Hardcoded string '{arg.s}' in {path} for {func.attr}. Use I18N.get().")

# Patch AST to add parent links for easier analysis
for folder in UI_PATHS:
    for fname in os.listdir(folder):
        if not fname.endswith('.py'):
            continue
        path = os.path.join(folder, fname)
        with open(path, 'r') as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
