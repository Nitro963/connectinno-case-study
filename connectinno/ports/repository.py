import abc


class ObjectDoesNotExists(Exception):
    pass


class IRepository(metaclass=abc.ABCMeta):
    seen: set
