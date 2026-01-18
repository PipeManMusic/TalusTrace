import os, glob, importlib.util
import types
import pytest

def find_tool_classes():
    guides = {}
    for path in glob.glob('tools/*.py'):
        name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            continue
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and attr.endswith('Tool'):
                guide = getattr(obj, '__guide__', None)
                guides[attr] = guide
    return guides

def test_tools_have_guides():
    guides = find_tool_classes()
    missing = [k for k, v in guides.items() if v is None]
    assert not missing, f"Missing __guide__ for: {', '.join(missing)}"

def test_generate_manual(tmp_path):
    guides = find_tool_classes()
    manual = tmp_path / "generated_user_manual.md"
    with open(manual, 'w') as f:
        for tool, guide in guides.items():
            f.write(f"# {tool}\n")
            f.write(f"{guide}\n\n")
    assert manual.exists()
