"""Name and types for experiments"""

from enum import Enum
from typing import List
from pydantic import BaseModel
# pylint: disable=C0103

class ExperimentName(str, Enum):
    """Valid names of experiments"""

    svgp_vary_static_features = "svgp_vary_static_features"
    dgp_vary_static_features = "dgp_vary_static_features"
    dgp_vary_inducing_and_maxiter = "dgp_vary_inducing_and_maxiter"
    dgp_small_inducing_and_maxiter = "dgp_small_inducing_and_maxiter"
    svgp_small_inducing_and_maxiter = "svgp_small_inducing_and_maxiter"

    svgp_vary_standard = "svgp_vary_standard"
    dgp_vary_standard = "dgp_vary_standard"
    cached_instance = "cached_instance"

    # dryrun - models are not trained well, mostly for testing
    dryrun_svgp = "dryrun_svgp"

    # production names
    production_mrdgp_dynamic = "production_mrdgp_dynamic"
    production_mrdgp_static = "production_mrdgp_static"
    production_svgp_dynamic = "production_svgp_dynamic"
    production_svgp_static = "production_svgp_static"


class ExperimentConfig(BaseModel):
    """Settings for an experiment"""

    name: ExperimentName
    instance_id_list: List[str]
