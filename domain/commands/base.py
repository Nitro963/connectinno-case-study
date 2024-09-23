from typing import Literal
from pydantic import BaseModel, ConfigDict


class CommandBase(BaseModel):
    type: Literal['command']

    model_config = ConfigDict(frozen=True)
