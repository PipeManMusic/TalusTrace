import ast
import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', 'tests', 'docs', 'build', 'dist'}


def iter_python_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename.endswith('.py'):
                yield os.path.join(dirpath, filename)

def has_docstring(node):
    return bool(ast.get_docstring(node))

def check_file_for_docstrings(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=filepath)
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if not has_docstring(node):
                lineno = getattr(node, 'lineno', 1)
                missing.append((filepath, lineno, type(node).__name__, getattr(node, 'name', '<module>')))
    return missing

def test_all_code_has_docstrings():
    """Test that all modules, classes, and functions have docstrings."""
    all_missing = []
    for pyfile in iter_python_files(PROJECT_ROOT):
        all_missing.extend(check_file_for_docstrings(pyfile))
    if all_missing:
        msg = '\n'.join(f"{file}:{lineno} {kind} '{name}' missing docstring" for file, lineno, kind, name in all_missing)
        pytest.fail(f"Missing docstrings in the following locations:\n{msg}")
