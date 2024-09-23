import enum
from typing import Optional, ClassVar

from celery.states import READY_STATES
from pydantic import BaseModel, field_validator, Field


class TaskStatus(str, enum.Enum):
    pending = 'PENDING'
    received = 'RECEIVED'
    failure = 'FAILURE'
    retry = 'RETRY'
    revoked = 'REVOKED'
    started = 'STARTED'
    success = 'SUCCESS'


class TaskBase(BaseModel):
    DEFAULT_SUCCESS_ROUTING_KEY: ClassVar[str] = 'task-success'
    DEFAULT_FAILURE_ROUTING_KEY: ClassVar[str] = 'task-failure'

    task_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    status: TaskStatus = TaskStatus.received

    @property
    def is_ready(self) -> bool:
        return self.status.value in READY_STATES

    @field_validator('name', mode='after')
    def shorten_task_name(cls, v: str):  # noqa
        return v.split('.')[-1]


class TaskProgressEvent(TaskBase):
    DEFAULT_ROUTING_KEY: ClassVar[str] = 'task-progress-update'
    status: TaskStatus = TaskStatus.started
    routing_key: str = 'task-progress-update'
    msg_key: Optional[str] = None
