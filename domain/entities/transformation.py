import datetime
from dataclasses import dataclass, field
from typing import Optional

from corelib import timezone
from ..value_objects.transformation_type import TransformationType


@dataclass(kw_only=True)
class BaseTransformation:
    type: str | TransformationType
    created_at: Optional[datetime.datetime] = field(default_factory=timezone.now)
    id: Optional[int] = None
    image_id: Optional[int] = None

    def __hash__(self):
        return hash((self.id, self.image_id, self.type))


@dataclass(kw_only=True)
class RotateTransformation(BaseTransformation):
    angle: Optional[int]

    def __hash__(self):
        return hash((self.id, self.image_id, self.type))


@dataclass(kw_only=True)
class GrayScaleTransformation(BaseTransformation):
    def __hash__(self):
        return hash((self.id, self.image_id, self.type))


@dataclass(kw_only=True)
class ResizeTransformation(BaseTransformation):
    height: Optional[int]
    width: Optional[int]

    def __hash__(self):
        return hash((self.id, self.image_id, self.type))


types_map = {
    BaseTransformation: TransformationType.BASE.value,
    GrayScaleTransformation: TransformationType.GRAY_SCALE.value,
    RotateTransformation: TransformationType.ROTATE.value,
    ResizeTransformation: TransformationType.RESIZE.value,
}
