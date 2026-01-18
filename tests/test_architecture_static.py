import os, re, glob

def scan_forbidden_imports(folder, forbidden):
    for path in glob.glob(f'{folder}/*.py'):
        with open(path) as f:
            code = f.read()
        for word in forbidden:
            if re.search(rf'^\s*import {word}|^\s*from {word}', code, re.MULTILINE):
                return path, word
    return None, None

def test_core_independence():
    path, word = scan_forbidden_imports('core', ['ui', 'PySide6'])
    assert not path, f"core/{os.path.basename(path)} imports {word}"

def test_infra_independence():
    path, word = scan_forbidden_imports('infra', ['ui'])
    assert not path, f"infra/{os.path.basename(path)} imports {word}"
