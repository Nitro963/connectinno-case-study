import datetime
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, HttpUrl

from domain.value_objects.transformation_type import TransformationType


@dataclass
class ImageModel:
    name: Optional[str] = None
    location: Optional[str] = None
    transformation_count: int = 0
    transformations: list = field(default_factory=list)
    created_at: Optional[datetime.datetime] = None
    id: Optional[int] = None

    def __hash__(self):
        return hash((self.id, self.location))

    def __repr__(self):
        return (
            f"ImageModel(name='{self.name}', location='{self.location}', "
            f'transformation_count={self.transformation_count},'
        )


class ImageUrl(BaseModel):
    id: int
    url: HttpUrl


class RankedImage(BaseModel):
    id: int
    original_filename: str
    rank: int


class TransformedImage(BaseModel):
    id: int
    original_filename: str
    transformation_type: Optional[TransformationType]
    transformation_timestamp: Optional[datetime.datetime]
