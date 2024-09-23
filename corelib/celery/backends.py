import orjson
from celery.backends.redis import RedisBackend as BackendBase
from celery.exceptions import BackendStoreError


class RedisBackend(BackendBase):
    def set(self, key, value, **retry_policy):
        if isinstance(value, str):
            res = orjson.loads(value)
            del res['kwargs']
            del res['args']
            value = orjson.dumps(res)
            if len(value) > self._MAX_STR_VALUE_SIZE:
                raise BackendStoreError('value too large for Redis backend')
        return self.ensure(self._set, (key, value), **retry_policy)

    @staticmethod
    def build_default_task_key(task_id: str):
        return ''.join(['celery-task-meta-', str(task_id)])
