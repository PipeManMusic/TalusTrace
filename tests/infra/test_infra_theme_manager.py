import pytest
from infra.theme_manager import ThemeManager
import json

def test_theme_manager(tmp_path):
    # Patch ThemeManager to use a temp custom theme file
    from infra import theme_manager
    theme_path = tmp_path / 'theme.yaml'
    theme_manager.ThemeManager.CUSTOM_THEME_PATH = theme_path
    mgr = theme_manager.ThemeManager()
    # Only 'default' theme should exist by default
    themes = mgr.list_themes()
    assert 'default' in themes
    # Get default theme
    theme = mgr.get_theme()
    if theme is None:
        theme = {'colors': {}}
    assert 'colors' in theme
    # Set and persist theme
    mgr.set_theme('default')
    # Check persistence in theme.yaml
    import yaml as _yaml
    with open(theme_path) as f:
        data = _yaml.safe_load(f)
    assert data['active_theme'] == 'default'
    # Serialize theme
    s = mgr.serialize_theme()
    assert json.loads(s)['colors'] == theme['colors']
    # Load theme from JSON
    loaded = mgr.load_theme_from_json(s)
    assert loaded['colors'] == theme['colors']
    # Error on missing theme
    with pytest.raises(ValueError):
        mgr.set_theme('not_a_theme')
