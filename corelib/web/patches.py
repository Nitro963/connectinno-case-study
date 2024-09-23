import asyncio
import functools
import logging
import time
from inspect import isfunction

from pydantic import ValidationError
from pydantic_core import PydanticCustomError
from sentry_sdk import capture_exception
from corelib.web.constants import (
    HTTP_501_NOT_IMPLEMENTED_EXCEPTION,
    HTTP_504_GATEWAY_TIMEOUT_EXCEPTION,
    HTTP_503_SERVICE_UNAVAILABLE_EXCEPTION,
)


def sio_execute(coro):
    @functools.wraps(coro)
    async def wrapper(*args, **kwargs):
        from .config import get_settings

        settings = get_settings()
        st = time.time()
        sid = args[0] if args else 'Unknown'
        code = 200
        try:
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
        except ValidationError as e:
            code = 422
            return 'ValidationError', code, e.json()
        except PydanticCustomError as e:
            code = 400
            return 'BadRequest', code, e.message()
        except Exception as e:
            logging.getLogger('uvicorn.error').error('Something happened', exc_info=e)
            if settings.SENTRY_DSN:
                capture_exception(e)
            return 'Server Internal Error', 500, str(e) if settings.DEBUG else None
        finally:
            logging.getLogger('uvicorn.error').info(
                f'event "{coro.__name__}" [{sid}] {code} in {(time.time() - st) * 1000:0.3f} ms'
            )

    return wrapper


# TODO add validation error handler and internal server error handler
async def not_implemented_exception_handler(request, exc):
    raise HTTP_501_NOT_IMPLEMENTED_EXCEPTION


async def timeout_exception_handler(request, exc):
    raise HTTP_504_GATEWAY_TIMEOUT_EXCEPTION


async def unavailable_exception_handler(request, exc):
    raise HTTP_503_SERVICE_UNAVAILABLE_EXCEPTION


__all__ = [
    'unavailable_exception_handler',
    'timeout_exception_handler',
    'not_implemented_exception_handler',
    'sio_execute',
]
