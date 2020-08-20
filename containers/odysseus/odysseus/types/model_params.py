"""Pydantic for model parameters."""

from typing import Optional
from pydantic import BaseModel
from cleanair.types.model_types import ParamIdMixin

class KernelParams(BaseModel):

    lengthscales: float
    period: Optional[float]     # for the periodic kernel
    variance: float

class ScootModelParams(ParamIdMixin, BaseModel):

    kernel: KernelParams
    maxiter: int

class SparseVariationalParams(ScootModelParams):

    n_inducing_points: int

