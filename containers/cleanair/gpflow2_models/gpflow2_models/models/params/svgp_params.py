"""Default parameters for the SVGP"""

from typing import List, Optional
from .shared_params import (
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    MINIBATCH_SIZE,
    KERNEL_VARIANCE,
)
from ...types.enum_types import Source, Species
from ...types.model_types import SVGPParams, KernelParams

JITTER: float = 1e-5
SVGP_NUM_INDUCING_POINTS = 2000
SVGP_INPUT_DIM = 3
SVGP_MAXITER = 15000

# production data config settings for the svgp
PRODUCTION_SVGP_TRAIN_DAYS = 5
PRODUCTION_SVGP_TRAIN_SOURCES = [Source.laqn]
PRODUCTION_SVGP_FORECAST_SOURCES = [Source.laqn, Source.hexgrid]
PRODUCTION_SVGP_TRAIN_INTEREST_POINTS = {Source.laqn: "all"}
PRODUCTION_SVGP_FORECAST_INTEREST_POINTS = {Source.laqn: "all", Source.hexgrid: "all"}
PRODUCTION_SVGP_SPECIES = [Species.NO2]


def default_svgp_kernel():
    pass


def default_svgp_model_params():
    pass
