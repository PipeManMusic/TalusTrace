import pytest
import yaml
# Target Implementation: ui/panels/library.py
from ui.panels.library import LibraryLoader

@pytest.fixture
def temp_library(tmp_path):
    data = {
        "parts": {
            "TEST-PART-01": {
                "manufacturer": "TestCorp",
                "description": "A Test Connector"
            }
        }
    }
    path = tmp_path / "parts.yaml"
    with open(path, 'w') as f:
        yaml.dump(data, f)
    return str(path)

def test_library_loader(temp_library):
    loader = LibraryLoader(library_path=temp_library)
    items = loader.get_items()
    
    assert "TEST-PART-01" in items
    assert items["TEST-PART-01"]["manufacturer"] == "TestCorp"