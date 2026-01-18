import pytest
import pkgutil
import inspect
import importlib
import sys
from pathlib import Path
from PySide6.QtWidgets import QGraphicsItem
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin

# --- 1. DYNAMIC DISCOVERY LOGIC ---
def discover_view_classes():
    """
    Scans the 'ui/items' folder and returns a list of all 
    QGraphicsItem subclasses found in the files.
    """
    project_root = Path(__file__).parent.parent
    items_pkg = project_root / "ui" / "items"
    
    # Ensure project root is in python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    found_classes = []
    found_names = []

    for module_info in pkgutil.iter_modules([str(items_pkg)]):
        module_name = f"ui.items.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            pytest.fail(f"DISCOVERY ERROR: Could not import '{module_name}'. Error: {e}")

        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module_name:
                if issubclass(cls, QGraphicsItem) and cls is not ObservableGraphicsItemMixin:
                    found_classes.append(cls)
                    found_names.append(cls.__name__)

    # CRITICAL: Fail if core classes are missing
    required_classes = ["WireItem", "DeviceItem"]
    missing = [req for req in required_classes if req not in found_names]
    if missing:
        pytest.fail(f"DISCOVERY ERROR: Could not find classes: {missing}. Check imports.")

    return found_classes

# Run discovery once
ALL_VIEW_ITEMS = discover_view_classes()

# --- 2. THE META-TESTS (The Laws) ---

@pytest.mark.parametrize("item_class", ALL_VIEW_ITEMS)
def test_contract_compliance_data(item_class):
    """
    META-TEST: Verifies that the class defines its own test data.
    If this fails, it means you haven't implemented the tests for this item yet.
    """
    if not hasattr(item_class, "__test_scenario__"):
        pytest.fail(
            f"MISSING CONTRACT: Class '{item_class.__name__}' does not define '__test_scenario__'.\n"
            f"You must add this dictionary to the class to define how it should be verified.\n"
            f"Example:\n"
            f"    class {item_class.__name__}(...):\n"
            f"        __test_scenario__ = {{ 'model_data': {{...}}, 'expected_child_count': 0 }}"
        )

@pytest.mark.parametrize("item_class", ALL_VIEW_ITEMS)
def test_contract_compliance_mvc_rules(item_class):
    """
    META-TEST: Enforces strict MVC rules.
    If this fails, the class is too 'smart' and needs a lobotomy.
    """
    # 1. Check for Forbidden Events
    forbidden = [
        "mousePressEvent", "mouseReleaseEvent", "mouseDoubleClickEvent",
        "keyPressEvent", "wheelEvent", "contextMenuEvent"
    ]
    defined_methods = item_class.__dict__
    
    for method in forbidden:
        if method in defined_methods:
            pytest.fail(
                f"MVC VIOLATION: '{item_class.__name__}' defines '{method}'.\n"
                f"Views must be DUMB. Move this logic to a Tool."
            )

    # 2. Check for Observable Mixin
    if not issubclass(item_class, ObservableGraphicsItemMixin):
        pytest.fail(
            f"ARCH VIOLATION: '{item_class.__name__}' does not inherit 'ObservableGraphicsItemMixin'.\n"
            f"It cannot receive API updates."
        )
