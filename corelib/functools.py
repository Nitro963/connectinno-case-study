import asyncio
import functools
from inspect import isfunction

from .functional import pipeline_func


def delayed(seconds=1):
    def decorator(coro):
        @functools.wraps(coro)
        async def wrapper(*args, **kwargs):
            await asyncio.sleep(seconds)
            if coro is None:
                return None
            if asyncio.iscoroutinefunction(coro):
                return await coro(*args, **kwargs)
            if isfunction(coro):
                return coro(*args, **kwargs)
            if asyncio.isfuture(coro):
                return await coro  # noqa
            if asyncio.iscoroutine(coro):
                return await coro  # noqa
            assert False

        return wrapper

    return decorator


def piped(f):
    class _CallablePipe(pipeline_func):
        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    wrapper = _CallablePipe(f)
    functools.update_wrapper(wrapper, f)
    return wrapper


__all__ = [
    'delayed',
    'piped',
]
