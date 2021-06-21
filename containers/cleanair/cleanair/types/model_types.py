"""Types for models and parameters."""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from .enum_types import KernelType, ModelName


class KernelParams(BaseModel):
    """Validation for kernel parameters."""

    name: str
    type: KernelType
    active_dims: Optional[List[int]]
    lengthscales: Optional[Union[float, List[float]]]
    variance: Optional[Union[float, List[float]]]
    ARD: Optional[bool]
    input_dim: int  # cannot be Optional/None due to gpflow error


class BaseModelParams(BaseModel):
    """Validation of a (sub) model parameters."""

    kernel: Union[KernelParams, List[KernelParams]]
    likelihood_variance: float
    num_inducing_points: int
    maxiter: int
    minibatch_size: int


class SVGPParams(BaseModelParams):
    """Model parameters for the SVGP."""

    jitter: float


class MRDGPParams(BaseModel):
    """Model parameters for the Deep GP."""

    base_laqn: BaseModelParams
    base_sat: BaseModelParams
    dgp_sat: BaseModelParams
    mixing_weight: Dict[str, Union[str, None]]
    num_prediction_samples: int
    num_samples_between_layers: int


class CompiledMRDGPParams(BaseModel):

    base_laqn: List[KernelParams]
    base_sat: List[KernelParams]
    dgp_sat: List[KernelParams]
    mixing_weight: Dict[str, Union[str, None]]
    num_prediction_samples: int
    num_samples_between_layers: int


def model_params_from_dict(
    model_name: ModelName, params_dict: Dict
) -> Union[SVGPParams, MRDGPParams]:
    """Use the model name to return the right type of model params"""
    if model_name == ModelName.svgp:
        return SVGPParams(**params_dict)
    if model_name == ModelName.mrdgp:
        return MRDGPParams(**params_dict)
    raise ValueError(f"{model_name} is not a valid model name")
