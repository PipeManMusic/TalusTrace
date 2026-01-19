import yaml
import os

class I18N:
    _strings = None
    _lang = 'en'
    _lang_path = os.path.join(os.path.dirname(__file__), '../resources/config/langs/en.yaml')

    @classmethod
    def load(cls, lang=None):
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
        if cls._strings is None:
            cls.load()
        val = cls._strings.get(key, default if default is not None else key)
        if kwargs and isinstance(val, str):
            return val.format(**kwargs)
        return val
