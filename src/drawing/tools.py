from enum import Enum


class Tool(Enum):
    BRUSH = "brush"
    ERASER = "eraser"
    SHAPE = "shape"
    FILL = "fill"
    EYEDROPPER = "eyedropper"
    SELECT = "select"


class ShapeType(Enum):
    RECTANGLE = "rectangle"
    OVAL = "oval"
    LINE = "line"
    TRIANGLE = "triangle"
    HEART = "heart"
    STAR = "star"
