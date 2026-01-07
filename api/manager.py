from infra.context import ProjectContext

class APIManager:
    _instance = None

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.context = ProjectContext()
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
