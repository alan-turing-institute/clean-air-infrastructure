"""Test kernel params are parsed correctly."""

from __future__ import annotations
from typing import TYPE_CHECKING
import gpflow
from odysseus.modelling import parse_kernel

if TYPE_CHECKING:
    from odysseus.types import KernelParams, PeriodicKernelParams


def test_parse_kernel(matern32: KernelParams) -> None:
    """Test a single kernel is parsed correctly."""
    kernel: gpflow.kernels.Matern32 = parse_kernel(matern32)
    assert isinstance(kernel, gpflow.kernels.Matern32)


def test_parse_kernel_product(
    matern32: KernelParams, periodic: PeriodicKernelParams
) -> None:
    """Test a list of kernel params can be parsed."""
    product = [matern32, periodic]
    kernel = parse_kernel(product)
    assert isinstance(kernel, gpflow.kernels.Kernel)
