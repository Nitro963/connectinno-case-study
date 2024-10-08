class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    @property
    def instance(cls):
        if cls not in cls._instances:
            return cls.__call__()
        return cls._instances[cls]
