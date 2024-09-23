import asyncio
from typing import Optional

import orjson
from celery.states import READY_STATES
from redis.asyncio import Redis as AsyncRedis
from corelib.celery.task import TaskBase
from .keys import KeysGeneratorBase


async def get_celery_task(client: AsyncRedis, task_id: str) -> Optional[str]:
    return await client.get(KeysGeneratorBase.celery_task(task_id))


async def is_celery_task_ready(client: AsyncRedis, task_id: str) -> bool:
    obj = await client.get(KeysGeneratorBase.celery_task(task_id))
    assert obj, 'Task not found.'
    obj = orjson.loads(obj)
    return obj['status'] in READY_STATES


# Wait a Celery task in an async fashion without relying on event loop executor
# Of course, this is not a perfect solution since it relies on polling,
# but it is a good workaround until Celery officially provides a better solution.
async def wait_celery_task(
    client: AsyncRedis, task_id: str, timeout: Optional[float] = None
) -> Optional[str]:
    delay = 0.1
    while True:
        if delay > timeout:
            raise TimeoutError()
        async_result = await get_celery_task(client, task_id)
        if not async_result:
            return None
        ready = TaskBase.model_validate_json(async_result).is_ready
        if ready:
            return async_result
        await asyncio.sleep(delay)
        delay = min(delay * 1.5, 2)  # exponential backoff, max 2 seconds


__all__ = [
    'wait_celery_task',
    'is_celery_task_ready',
    'get_celery_task',
]
