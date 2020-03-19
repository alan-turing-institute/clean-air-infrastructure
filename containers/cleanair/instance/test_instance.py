"""
Instances for testing the cleanair package.
"""
from .validation_instance import ValidationInstance

class LaqnTestInstance(ValidationInstance):
    """
    A quick test only on LAQN data that trains for 1 days and predicts for 1 day.
    """

    DEFAULT_DATA_CONFIG = dict(
        ValidationInstance.DEFAULT_DATA_CONFIG,
        include_satellite=False,
        include_prediction_y=False,
        tag="test",
    )

    DEFAULT_MODEL_PARAMS = dict(
        ValidationInstance.DEFAULT_MODEL_PARAMS,
        maxiter=1,
    )

    DEFAULT_MODEL_NAME = "svgp"
