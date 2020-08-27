"""Fixtures for modelling."""

import pytest
from odysseus.types.model_params import KernelParams, PeriodicKernelParams, ScootModelParams

#pylint: disable=redefined-outer-name

@pytest.fixture(scope="function")
def matern32() -> KernelParams:
    """Matern 32 kernel params."""
    return KernelParams(name="matern32", lengthscales=0.1, variance=2.0)

@pytest.fixture(scope="function")
def periodic(matern32: KernelParams) -> PeriodicKernelParams:
    """Matern 32 kernel params."""
    return PeriodicKernelParams(name="periodic", period=5, base_kernel=matern32)

@pytest.fixture(scope="function")
def gpr_params(matern32) -> ScootModelParams:
    """Params for a GPR with Matern32 kernel."""
    return ScootModelParams(maxiter=100, kernel=matern32)
