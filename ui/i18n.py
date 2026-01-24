"""
Internationalization (i18n) utilities for Talus Trace UI.

Loads and retrieves localized strings from YAML files.
"""

import yaml
import os

class I18N:
    """Handles loading and retrieval of localized UI strings."""
    _strings = None
    _lang = 'en'
    _lang_path = os.path.join(os.path.dirname(__file__), '../resources/config/langs/en.yaml')

    @classmethod
    def load(cls, lang=None):
        """Load language strings from a YAML file for the given language code."""
        if lang:
            cls._lang = lang
            cls._lang_path = os.path.join(os.path.dirname(__file__), f'../resources/config/langs/{lang}.yaml')
        try:
            with open(cls._lang_path, 'r') as f:
                cls._strings = yaml.safe_load(f) or {}
        except Exception:
            cls._strings = {}

    @classmethod
    def get(cls, key, default=None, **kwargs):
        """Retrieve a localized string by key, formatting with kwargs if provided."""
        if cls._strings is None:
            cls.load()
        val = cls._strings.get(key, default if default is not None else key)
        if kwargs and isinstance(val, str):
            return val.format(**kwargs)
        return val
