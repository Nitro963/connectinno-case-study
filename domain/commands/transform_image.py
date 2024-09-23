from typing import Literal, Annotated

from pydantic import BaseModel, Field

from domain import Command
from domain.value_objects.transformation_type import TransformationType
from domain.entities import transformation


class ImageRotation(BaseModel):
    type: Literal[TransformationType.ROTATE]
    angle: int = Field(..., gt=0, le=360)

    def to_domain(self) -> transformation.RotateTransformation:
        return transformation.RotateTransformation(angle=self.angle, type=self.type)


class ImageResize(BaseModel):
    type: Literal[TransformationType.RESIZE]
    height: int = Field(..., le=4096, ge=1)
    width: int = Field(..., le=4096, ge=1)

    def to_domain(self) -> transformation.ResizeTransformation:
        return transformation.ResizeTransformation(
            width=self.width, height=self.height, type=self.type
        )


class GrayScaleImage(BaseModel):
    type: Literal[TransformationType.GRAY_SCALE]

    def to_domain(self):
        return transformation.GrayScaleTransformation(type=self.type)


ImageTransformation = Annotated[
    ImageResize | ImageRotation | GrayScaleImage, Field(..., discriminator='type')
]


class TransformImageCommand(Command):
    type: Literal['transform-image-command'] = 'transform-image-command'
    image_id: int
    transformations: list[ImageTransformation]
