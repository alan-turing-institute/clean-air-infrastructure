"""Types for models and parameters."""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, validator

KernelDict = Dict[str, Union[str, float, List[Union[int, float]]]]
ParamsDict = Dict[str, Union[float, bool, int, KernelDict, List[KernelDict]]]

class KernelParams(BaseModel):
    """Validation for kernel parameters."""

    name: str
    type: str
    active_dims: Optional[List[int]]
    lengthscales: Optional[Union[float, List[float]]]
    variance: Optional[Union[float, List[float]]]

class BaseModelParams(BaseModel):
    """Validation of a (sub) model parameters."""
    kernel: Union[KernelParams, List[KernelParams]]
    likelihood_variance: float
    num_inducing_points: int
    minibatch_size: int

class SVGPParams(BaseModelParams):
    """Model parameters for the SVGP."""
    jitter: float
    maxiter: int

class MRDGPParams(BaseModel):
    """Model parameters for the Deep GP."""
