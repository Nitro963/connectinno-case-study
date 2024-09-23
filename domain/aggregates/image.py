from io import BytesIO
from typing import Optional

from fsspec import AbstractFileSystem
from pydantic import BaseModel, ConfigDict

from domain.entities import ImageModel
import PIL
from PIL.Image import Image


class ImageAggregate(BaseModel):
    image_info: ImageModel
    fs: AbstractFileSystem
    image: Optional[Image] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def load(self):
        with self.fs.open(self.image_info.location) as f:
            self.image = PIL.Image.open(BytesIO(f.read()))
        return self

    def __hash__(self):
        return self.image_info.__hash__()
