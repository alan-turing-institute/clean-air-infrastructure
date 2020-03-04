"""
The instance to run in production.
"""

from .runnable import RunnableInstance

class ProductionInstance(RunnableInstance):

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": True,
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

    DEFAULT_EXPERIMENT_CONFIG = {
        "model_name": "mr_dgp",
        "secretfile": "../../terraform/.secrets/db_secrets.json",
        "results_dir": "./",
        "model_dir": "./",
        "config_dir": "./",
        "local_read": False,
        "local_write": False,
        "predict_training": False,
        "predict_write": False,
        "no_db_write": False,
        "restore": False,
        "save_model_state": False,
    }

    DEFAULT_MODEL_PARAMS = {"restore": False, "train": True, "model_state_fp": "", "maxiter": 10}

    DEFAULT_MODEL_NAME = "mr_dgp"

    def __init__(self, **kwargs):
        if "tag" in kwargs and kwargs["tag"] != "production":
            raise AttributeError("The tag must be 'production' when running a production instance.")
        super().__init__(**kwargs)
        