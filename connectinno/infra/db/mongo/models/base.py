from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field

from corelib import timezone


class BaseModel(PydanticBaseModel):
    id: PydanticObjectId = Field(..., alias='_id')
    created_at: datetime = Field(default_factory=timezone.now)

    model_config = ConfigDict(from_attributes=True)

    def flatten(self):
        return str(self.id)
