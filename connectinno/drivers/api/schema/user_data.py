from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator, Field
from pydantic_core.core_schema import ValidationInfo


class UserType(str, Enum):
    user = 'user'


class UserDataBase(BaseModel):
    auth_id: str = Field(..., alias='id')
    user_type: UserType

    @field_validator('auth_id', mode='before')  # noqa
    @classmethod
    def validate_auth_id(cls, v, _info: ValidationInfo):
        if isinstance(v, int):
            return str(v)
        return v


class UserData(UserDataBase):
    info_payload: Optional[dict] = {}


__all__ = [
    'UserData',
    'UserDataBase',
    'UserType',
]
