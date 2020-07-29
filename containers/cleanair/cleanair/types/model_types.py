"""Types for models and parameters."""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from ..utils import hash_dict

KernelDict = Dict[str, Union[str, float, List[Union[int, float]]]]
ParamsDict = Dict[str, Union[float, bool, int, KernelDict, List[KernelDict]]]


class ParamIdMixin:
    """Add function for creating a param id."""

    def param_id(self):
        """Return a hashed param id."""
        return hash_dict(self.json(sort_keys=True))


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
    maxiter: int
    minibatch_size: int


class SVGPParams(ParamIdMixin, BaseModelParams):
    """Model parameters for the SVGP."""

    jitter: float


class MRDGPParams(ParamIdMixin, BaseModel):
    """Model parameters for the Deep GP."""

    base_laqn: BaseModelParams
    base_sat: BaseModelParams
    dgp_sat: BaseModelParams
    mixing_weight: Dict[str, Union[str, None]]
    num_prediction_samples: int
    num_samples_between_layers: int
