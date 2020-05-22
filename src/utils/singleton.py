class Singleton:
    def __init__(self, cls):
        self._cls = cls
        self._instance = None

    def instance(self):
        if self._instance is None:
            self._instance = self._cls()
        return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._cls)
