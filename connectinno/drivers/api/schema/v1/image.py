import datetime

from pydantic import BaseModel, ConfigDict


class ImageInfo(BaseModel):
    id: int
    name: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True, frozen=True)
