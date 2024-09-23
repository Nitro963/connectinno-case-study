import enum

from pydantic import BaseModel


class ErrorModel(BaseModel):
    detail: str


class ProcessingResult(int, enum.Enum):
    ok = 1
    error = 2
