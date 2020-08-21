"""Creating gpflow kernels."""

from __future__ import annotations
from typing import Dict
import gpflow
from ..types.model_params import KernelParams, KernelProduct

def parse_kernel_token(next_token: KernelProduct, kernel_map: Dict[str, gpflow.kernels.Kernel]) -> gpflow.kernels.Kernel:
    """Parser kernel tokens.

    Args:
        next_token: The token to parse.
        kernel_map: Mapping from kernel names to gpflow kernels.

    Returns:
        An initialised gpflow kernel.
    """
    # return gpflow kernel from params
    if isinstance(next_token, KernelParams):
        kernel_params = next_token.dict()
        kernel_params.pop("name")
        print(kernel_params)
        return kernel_map[next_token.name](**kernel_params)

    kernel = None
    # take produce of kernels in list
    for item in next_token:
        if not kernel:
            kernel = parse_kernel_token(item, kernel_map)
        else:
            kernel = kernel * parse_kernel_token(item, kernel_map)
    return kernel

def parse_kernel(token: KernelProduct) -> gpflow.kernels.Kernel:
    """Creates a mapping of kernel names to gpflow kernels then parse the token.

    Args:
        token: Either a list of KernelParams or a single KernelParams.
            If a list is passed then the product of the kernels is created.

    Returns:
        An initialised gpflow kernel.
    """
    mod = gpflow.kernels
    kernel_map = dict(
        [
            (name.lower(), cls)
            for name, cls in mod.__dict__.items()
            if isinstance(cls, type)
        ]
    )
    return parse_kernel_token(token, kernel_map)
