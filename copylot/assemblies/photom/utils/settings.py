import os
from typing import List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    Extra,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    root_validator,
    validator,
)


# All settings classes inherit from MyBaseModel, which forbids extra parameters to guard against typos
class MyBaseModel(BaseModel, extra=Extra.forbid):
    pass


class AffineTransformationSettings(MyBaseModel):
    affine_transform_yx: list[list[float]]
    # TODO: validations for the affine transform matrix
