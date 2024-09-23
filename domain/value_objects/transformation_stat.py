from pydantic import BaseModel

from .transformation_type import TransformationType


class TransformationByType(BaseModel):
    type: TransformationType
    count: int
