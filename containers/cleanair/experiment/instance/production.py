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

    DEFAULT_MODEL_PARAMS = {"restore": False, "train": True, "model_state_fp": "", "maxiter": 10}

    def __init__(self, data_config=None, experiment_config=None, model_params=None, **kwargs):
        # ToDo: check that version is master and tag is production
        if "tag" in kwargs and kwargs["tag"] != "production":
            raise AttributeError("The tag must be 'production' when running a production instance. Change to a different instance if not running production code.")

        super().__init__(data_config=data_config, experiment_config=experiment_config, model_params=model_params, **kwargs)

    def setup_model(self):
        self.model = self.__class__.MODELS[self.model_name](
            experiment_config=self.experiment_config,
            model_params=self.model_params,
        )

    def setup_data(self):
        self.model_data = ModelData(
            config=self.data_config,
            secretfile=self.experiment_config["secretfile"],
        )

    def run_model_fitting(self):
        training_data_dict = self.model_data.get_training_data_arrays(dropna=False)
        x_train = training_data_dict["X"]
        y_train = training_data_dict["Y"]

        self.fit_start_time = datetime.now()
        self.model.fit(x_train, y_train)

    def run_prediction(self):
        predict_data_dict = self.model_data.get_pred_data_arrays(dropna=False)
        x_test = predict_data_dict["X"]
        return self.model.predict(x_test)

    def update_results(self, y_pred):
        self.model_data.update_test_df_with_preds(y_pred, self.fit_start_time)