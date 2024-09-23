from enum import Enum


class TransformationType(str, Enum):
    BASE = 'base-transformation'
    ROTATE = 'rotate-transformation'
    GRAY_SCALE = 'gray-scale-transformation'
    RESIZE = 'resize-transformation'
