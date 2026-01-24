import pytest
import yaml
import os
from ui.main_window import MainWindow
from api.manager import APIManager
from infra.context import Context
from api.actions import registry
from PySide6.QtWidgets import QApplication
from unittest.mock import patch

LANG_DIR = "resources/config/langs"
DEFAULT_LANG = "en"

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    yield api

@pytest.fixture(scope="function")
def main_window(app, api_manager):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    window.show()
    yield window
    window.close()

def get_menu_items_with_labels():
    with open("resources/config/ui_layout.yaml", "r") as f:
        config = yaml.safe_load(f)
    items = []
    for menu in config.get("menubar", []):
        for item in menu.get("items", []):
            if isinstance(item, dict) and "command" in item:
                items.append(item)
    return items

def get_lang_yaml(lang=DEFAULT_LANG):
    lang_path = os.path.join(LANG_DIR, f"{lang}.yaml")
    if not os.path.exists(lang_path):
        return {}
    with open(lang_path, "r") as f:
        return yaml.safe_load(f) or {}

@pytest.mark.gui
def test_menu_items_have_translatable_label():
    items = get_menu_items_with_labels()
    missing = [item["command"] for item in items if "label" not in item]
    assert not missing, f"Menu items missing 'label' for i18n: {missing}"

@pytest.mark.gui
def test_menu_labels_exist_in_language_yaml():
    items = get_menu_items_with_labels()
    lang_yaml = get_lang_yaml(DEFAULT_LANG)
    missing = [item["label"] for item in items if item["label"] not in lang_yaml]
    assert not missing, f"Missing translations in {DEFAULT_LANG}.yaml: {missing}"

@pytest.mark.gui
def test_menu_labels_render_translated(main_window):
    lang_yaml = get_lang_yaml(DEFAULT_LANG)
    menubar = main_window.menuBar()
    for action in menubar.actions():
        menu = action.menu()
        if menu:
            for act in menu.actions():
                label = act.text()
                assert label in lang_yaml.values(), f"Menu label '{label}' not translated from yaml."
