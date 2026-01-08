import pytest
import re
from pathlib import Path

# Industrial Hex Regex: Matches #FFF or #FFFFFF
HEX_REGEX = re.compile(r'#(?:[0-9a-fA-F]{3}){1,2}\b')

def test_ph4_theming_compliance_no_hardcoded_hex():
    """
    Mandate Audit: UI components must be 'Dumb Visualizers' and
    cannot contain hardcoded design choices (hex codes).
    """
    ui_path = Path("ui")
    violations = []

    # Target only Python files in the UI layer
    for python_file in ui_path.rglob("*.py"):
        # Skip __pycache__ or temporary files
        if "__pycache__" in str(python_file):
            continue
            
        with open(python_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # Check for hex codes
                matches = HEX_REGEX.findall(line)
                
                # Filter out lines that are actually referencing the theme engine
                # e.g., "return QColor('#FF00FF')" in the fallback logic is allowed 
                # only in coordinates.py as a last resort.
                if matches and "coordinates.py" not in str(python_file):
                    violations.append(
                        f"{python_file.name}:{line_num} -> Found {matches}"
                    )

    if violations:
        error_msg = "\n".join([
            "❌ THEME VIOLATION: Hardcoded hex codes found in UI logic.",
            "Move these to data/theme.json and use transformer.get_color().",
            *violations
        ])
        pytest.fail(error_msg)

def test_theme_fallback_integrity():
    """
    Ensures the transformer provides a 'Missing Texture' color (Magenta)
    instead of crashing when a key is missing.
    """
    from ui.coordinates import CoordinateTransformer
    transformer = CoordinateTransformer()
    
    # Request a key that definitely doesn't exist
    missing_color = transformer.get_color("non_existent_key_999")
    
    # Should return Magenta (#FF00FF) as a visual alert to the engineer
    assert missing_color.name().upper() == "#FF00FF"
    