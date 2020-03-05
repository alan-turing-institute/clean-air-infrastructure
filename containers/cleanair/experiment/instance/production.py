"""
The instance to run in production.
"""

from datetime import datetime
from ...models import ModelData
from .runnable import RunnableInstance

class ProductionInstance(RunnableInstance):

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        # ToDo: add satellite
        # "include_satellite": True,
        "include_satellite": False,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        # ToDo: add grid to pred sources
        # "pred_sources": ["laqn", "grid100"],
        "pred_sources": ["laqn"],
        "train_interest_points": "all",
        "train_satellite_interest_points": "all",
        "pred_interest_points": "all",
        "species": ["NO2"],
        # ToDo: add dynamic features
        "features": [
            "value_1000_total_a_road_length",
            "value_500_total_a_road_length",
            "value_500_total_a_road_primary_length",
            "value_500_total_b_road_length",
        ],
        "norm_by": "laqn",
        "tag": "production",
    }

    DEFAULT_MODEL_PARAMS = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 2000,
        "restore": False,
        "train": True,
        "model_state_fp": None,
        "maxiter": 100,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }

    def __init__(self, data_config=None, experiment_config=None, model_params=None, **kwargs):
        # ToDo: check that version is master and tag is production
        if "tag" in kwargs and kwargs["tag"] != "production":
            raise AttributeError("The tag must be 'production' when running a production instance. Change to a different instance if not running production code.")

        super().__init__(data_config=data_config, experiment_config=experiment_config, model_params=model_params, **kwargs)
