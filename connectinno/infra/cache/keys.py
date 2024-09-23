import functools
from typing import Optional

from corelib.cache import get_cache_settings
from corelib.patterns import Singleton


def prefixed_key(f):
    """
    A method decorator that prefixes return values.
    Prefixes any string that the decorated method `f` returns with the value of
    the `prefix` attribute on the owner object `self`.
    """

    @functools.wraps(f)
    def prefixed_method(self, *args, **kwargs):
        key = f(self, *args, **kwargs)
        # if Environments(os.environ.get('APP_ENV').upper()) == Environments.prod:
        #     key = sha256(key)
        return f'{self.prefix}:{key}'

    return prefixed_method


class KeysGeneratorBase(metaclass=Singleton):
    """Methods to generate key names for Redis data structures."""

    def __init__(self, prefix: Optional[str] = None, sep=','):
        self.prefix = prefix or get_cache_settings().REDIS_DEFAULT_KEY_PREFIX
        self.sep = sep

    @prefixed_key
    def connected_user(self, uid, user_type) -> str:
        return self.sep.join(['connected', str(user_type), str(uid)])

    @prefixed_key
    def connected_user_lock(self, uid, user_type) -> str:
        return self.sep.join(['user-lock', str(user_type), str(uid)])

    @prefixed_key
    def connection(self, sid):
        return self.sep.join(['connection', str(sid)])

    @prefixed_key
    def connection_lock(self, to):
        return self.sep.join(['connection-lock', str(to)])

    @prefixed_key
    def auth_token(self, token):
        return self.sep.join(['auth-token', token])

    @prefixed_key
    def user_has_permissions(self, uid, user_type):
        return self.sep.join(['user-has-permissions', str(user_type), str(uid)])

    @prefixed_key
    def connection_token(self, jti):
        return self.sep.join(['connection-token', str(jti)])

    @staticmethod
    def celery_task(task_id: str):
        return ''.join(('celery-task-meta-', str(task_id)))


__all__ = ['KeysGeneratorBase', 'prefixed_key']
