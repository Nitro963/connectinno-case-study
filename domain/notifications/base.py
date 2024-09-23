from typing import Literal

from pydantic import BaseModel


class NotificationBase(BaseModel):
    type: Literal['notification']
