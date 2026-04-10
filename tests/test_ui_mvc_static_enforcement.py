"""
Static analysis test for strict MVC enforcement in the UI layer.
Fails if any UI code directly mutates model objects or their attributes.
"""
import ast
import os
import pytest

# Directories to scan
UI_DIR = os.path.join(os.path.dirname(__file__), '../ui')
CORE_DIR = os.path.join(os.path.dirname(__file__), '../core')
INFRA_DIR = os.path.join(os.path.dirname(__file__), '../infra')

# Methods that mutate collections or objects
MUTATION_METHODS = {'append', 'remove', 'clear', 'pop', 'insert', 'update', 'setdefault', 'extend', 'add', 'discard'}

# Collect all model class names from core and infra
MODEL_CLASSES = set()
for mod_dir in [CORE_DIR, INFRA_DIR]:
    for fname in os.listdir(mod_dir):
        if fname.endswith('.py'):
            with open(os.path.join(mod_dir, fname), 'r') as f:
                try:
                    tree = ast.parse(f.read())
                except Exception:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        MODEL_CLASSES.add(node.name)


def find_model_mutations_in_ui():
    """Return a list of (filename, line, offending_code) for any UI file that directly mutates a model class or its attributes."""
    violations = []
    for root, _, files in os.walk(UI_DIR):
        for fname in files:
            if fname.endswith('.py'):
                path = os.path.join(root, fname)
                with open(path, 'r') as f:
                    try:
                        src = f.read()
                        tree = ast.parse(src)
                    except Exception:
                        continue
                for node in ast.walk(tree):
                    # Look for method calls like x.append(), x.remove(), etc.
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                        method = node.func.attr
                        if method in MUTATION_METHODS:
                            var = node.func.value
                            if isinstance(var, ast.Name):
                                varname = var.id
                                # Heuristic: if variable name is 'model', 'device', 'pin', etc., flag it
                                if any(model.lower() in varname.lower() for model in MODEL_CLASSES):
                                    violations.append((path, node.lineno, method))
                    # Look for direct assignment to model attributes
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Attribute):
                                if hasattr(target.value, 'id') and any(model.lower() in target.value.id.lower() for model in MODEL_CLASSES):
                                    violations.append((path, node.lineno, 'assign'))
    return violations



def test_ui_does_not_mutate_model():
    """Fail if any UI code directly mutates model objects or their attributes."""
    violations = find_model_mutations_in_ui()
    if violations:
        msg = '\n'.join(f"{file}:{lineno} {code}" for file, lineno, code in violations)
        pytest.fail(f"Direct model mutation found in UI code:\n{msg}")
