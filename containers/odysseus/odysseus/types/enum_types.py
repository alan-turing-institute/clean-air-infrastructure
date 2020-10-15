"""Enum types."""

from enum import Enum
import gpflow


class ScootModelName(Enum):
    """Models for scoot forecasting."""

    gpr: gpflow.models.GPR
    svgp: gpflow.models.SVGP
