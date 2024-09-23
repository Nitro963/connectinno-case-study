import asyncio

from celery import states
from celery.result import AsyncResult as _CeleryAsyncResult


class AsyncResult(_CeleryAsyncResult):
    @classmethod
    def from_base(cls, result: _CeleryAsyncResult):
        return cls(
            result.id, backend=result.backend, app=result.app, parent=result.parent
        )

    async def aget(
        self,
        timeout=None,
        propagate=True,
        interval=0.5,
        no_ack=True,
        follow_parents=True,
        callback=None,
        on_message=None,
        on_interval=None,
        disable_sync_subtasks=True,
        EXCEPTION_STATES=states.EXCEPTION_STATES,  # noqa # NOSONAR
        PROPAGATE_STATES=states.PROPAGATE_STATES,  # noqa # NOSONAR
    ):  # noqa # NOSONAR
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.get,
            timeout,
            propagate,
            interval,
            no_ack,
            follow_parents,
            callback,
            on_message,
            on_interval,
            disable_sync_subtasks,
            EXCEPTION_STATES,
            PROPAGATE_STATES,
        )


__all__ = ['AsyncResult']
