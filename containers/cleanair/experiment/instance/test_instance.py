
from .runnable import RunnableInstance
from ...models import ModelData, SVGP

class LaqnTestInstance(RunnableInstance):
    """
    A quick test only on LAQN data that trains for 1 days and predicts for 1 day.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": False,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        "pred_sources": ["laqn"],
        "train_interest_points": "all",
        "train_satellite_interest_points": "all",
        "pred_interest_points": "all",
        "species": ["NO2"],
        "features": [
            "value_1000_total_a_road_length",
            "value_500_total_a_road_length",
            "value_500_total_a_road_primary_length",
            "value_500_total_b_road_length",
        ],
        "norm_by": "laqn",
        "tag": "test",
    }

    DEFAULT_MODEL_PARAMS = {
        "model_name": "svgp",
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,
        "restore": False,
        "train": True,
        "model_state_fp": None,
        "maxiter": 1,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }

    def __init__(self, **kwargs):
        """
        Spin up a quick test instance that reads from the DB ready to run a simple GP.
        """
        xp_config = self.__class__.DEFAULT_EXPERIMENT_CONFIG
        model_data = ModelData(
            config=self.__class__.DEFAULT_DATA_CONFIG,
            secretfile=xp_config["secretfile"],
        )
        super().__init__(
            model_data=model_data,
            model_name="svgp",
            tag="test",
            model=SVGP(
                model_params=self.__class__.DEFAULT_MODEL_PARAMS,
                experiment_config=xp_config,
                tasks=["NO2"],
            ),
            cluster_id="laptop",
            experiment_config=xp_config
        )
