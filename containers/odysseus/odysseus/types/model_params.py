"""Pydantic for model parameters."""

from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel
from cleanair.types.model_types import ParamIdMixin

class KernelParams(BaseModel):
    """Parameters for a gpflow kernel."""

    name: str
    lengthscales: Optional[Union[float, List[float]]]
    variance: Optional[Union[float, List[float]]]

class PeriodicKernelParams(BaseModel):
    """Parameters for a periodic kernel."""
    name: str
    period: Optional[Union[float, List[float]]]
    base_kernel: KernelParams

KernelProduct = Union[KernelParams, PeriodicKernelParams, List[Union[KernelParams, PeriodicKernelParams]]]

class OptimizerName(str, Enum):
    """Supported optimizers."""

    adam = "adam"
    scipy = "scipy"

class ModelName(str, Enum):
    """Supported models."""

    gpr = "gpr"
    svgp = "svgp"

class ScootModelParams(ParamIdMixin, BaseModel):
    """Model parameters for a scoot GP model."""

    kernel: KernelProduct
    maxiter: int
    optimizer: OptimizerName

class SparseVariationalParams(ScootModelParams):
    """Model parameters for a SVGP."""

    n_inducing_points: int
