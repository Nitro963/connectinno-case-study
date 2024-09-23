import abc
from typing import TYPE_CHECKING, Optional

from PIL.Image import Image, Resampling
from domain.entities import transformation


class ITransformStrategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def execute(self, image):
        pass


class RotationStrategy(ITransformStrategy):
    def __init__(self, angle: int):
        self.angle = angle

    def execute(self, image: Image):
        return image.rotate(self.angle)


class GrayScaleStrategy(ITransformStrategy):
    def execute(self, image: Image):
        return image.convert(mode='L')


class ResizeStrategy(ITransformStrategy):
    def __init__(self, height: int, width: int):
        self.height = height
        self.width = width

    def execute(self, image: Image):
        return image.resize((self.width, self.height), Resampling.BICUBIC)


class Transformer:
    def __init__(self, strategy: Optional[ITransformStrategy] = None):
        self.strategy = strategy

    def transform(self, image):
        assert self.strategy, 'strategy must exists'
        return self.strategy.execute(image)

    def set_strategy(self, strategy: ITransformStrategy):
        self.strategy = strategy
        return self


_strategy_from_model_map = {
    transformation.BaseTransformation: None,
    transformation.ResizeTransformation: ResizeStrategy,
    transformation.RotateTransformation: RotationStrategy,
    transformation.GrayScaleTransformation: GrayScaleStrategy,
}


def strategy_from_model(model: transformation.BaseTransformation) -> ITransformStrategy:
    match model:
        case transformation.ResizeTransformation():
            if TYPE_CHECKING:
                assert isinstance(model, transformation.ResizeTransformation)
            assert model.height, 'height must exists'
            assert model.width, 'width must exists'
            return ResizeStrategy(height=model.height, width=model.width)
        case transformation.RotateTransformation():
            if TYPE_CHECKING:
                assert isinstance(model, transformation.RotateTransformation)
            assert model.angle is not None, 'angle must exists'
            return RotationStrategy(
                angle=model.angle,
            )
        case transformation.GrayScaleTransformation():
            return GrayScaleStrategy()
        case _:
            raise NotImplementedError()
