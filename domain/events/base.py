import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    id: str = Field(..., default_factory=uuid.uuid4)
    type: Literal['event']

    model_config = ConfigDict(frozen=True)
