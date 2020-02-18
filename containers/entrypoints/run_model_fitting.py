"""
Model fitting
"""
import os
import logging
import argparse
import pickle
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from cleanair.models import ModelData, SVGP
from cleanair.loggers import get_log_level


class CleanAirParser(argparse.ArgumentParser):
    """
    The base cleanair entrypoint parser.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-s",
            "--secretfile",
            default="../../terraform/.secrets/db_secrets.json",
            help="File with connection secrets.",
        )
        self.add_argument(
            "-d",
            "--config_dir",
            default="./",
            help="Filepath to directory to store model and data.",
        )
        self.add_argument("-v", "--verbose", action="count", default=0)


class ModelFitParser(CleanAirParser):
    """
    A parser for the model fitting entrypoint.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-results_dir",
            type=str,
            default=None,
            help="Filepath to the directory of results.",
        )
        self.add_argument(
            "-w",
            "--write",
            action="store_true",
            help="Write model data config to file.",
        )
        self.add_argument(
            "-r",
            "--read",
            action="store_true",
            help="Read model data from config_dir.",
        )
        self.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="Update the database with model results.",
        )
        self.add_argument(
            "-p",
            "--write_prediction",
            action="store_true",
            help="Write the predictions to file.",
        )
        self.add_argument(
            "-y",
            "--return_y",
            action="store_true",
            help="Include pollutant data in the test dataset.",
        )
        self.add_argument(
            "-t",
            "--predict_training",
            action="store_true",
            help="Predict on the training set.",
        )
        self.add_argument(
            "--trainend",
            type=str,
            default="2020-01-30T00:00:00",
            help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for training.",
        )
        self.add_argument(
            "--trainhours",
            type=int,
            default=48,
            help="The number of hours to get training data for.",
        )
        self.add_argument(
            "--predstart",
            type=str,
            default="2020-01-30T00:00:00",
            help="The first datetime (YYYY-MM-DD HH:MM:SS) to get model data for prediction.",
        )
        self.add_argument(
            "--predhours",
            type=int,
            default=48,
            help="The number of hours to predict for",
        )


def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()


def get_data_config(kwargs):
    """
    Return a dictionary of model data configs given parser arguments.
    """
    # Get training and pred start and end datetimes
    train_end = kwargs.pop("trainend")
    train_n_hours = kwargs.pop("trainhours")
    pred_start = kwargs.pop("predstart")
    pred_n_hours = kwargs.pop("predhours")
    train_start = strtime_offset(train_end, -train_n_hours)
    pred_end = strtime_offset(pred_start, pred_n_hours)
    return_y = kwargs.pop("return_y")

    # Model configuration
    model_config = {
        "train_start_date": train_start,
        "train_end_date": train_end,
        "pred_start_date": pred_start,
        "pred_end_date": pred_end,
        "include_satellite": True,
        "include_prediction_y": return_y,
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
        "model_type": "svgp",
        "tag": "testing_dashboard",
    }
    return model_config


def main():
    """
    Run model fitting
    """
    # Read command line arguments
    parser = ModelFitParser(description="Run model fitting")

    # Parse and interpret arguments
    args = parser.parse_args()
    kwargs = vars(args)

    # Update database/write to file
    update = kwargs.pop("update")
    write = kwargs.pop("write")
    read = kwargs.pop("read")
    write_prediction = kwargs.pop("write_prediction")
    results_dir = kwargs.pop("results_dir")
    predict_training = kwargs.pop("predict_training")

    # Set logging verbosity
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # get the model config from the parser arguments
    model_config = get_data_config(kwargs)

    if "aqe" in model_config["train_sources"] + model_config["pred_sources"]:
        raise NotImplementedError("AQE cannot currently be run. Coming soon")

    if model_config["species"] != ["NO2"]:
        raise NotImplementedError(
            "The only pollutant we can model right now is NO2. Coming soon"
        )

    # initialise the model
    model_fitter = SVGP(batch_size=1000)  # big batch size for the grid
    model_fitter.model_params["maxiter"] = 1
    model_fitter.model_params["model_state_fp"] = kwargs["config_dir"]

    # Get the model data
    if read:
        model_data = ModelData(**kwargs)
    else:
        model_data = ModelData(config=model_config, **kwargs)

    # write model results to file
    if write:
        model_data.save_config_state(kwargs["config_dir"])

    # get the training and test dictionaries
    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False)
    x_train = training_data_dict["X"]
    y_train = training_data_dict["Y"]
    x_test = predict_data_dict["X"]

    # Fit the model
    model_fitter.fit(x_train, y_train)

    # Get info about the model fit
    # model_fit_info = model_fitter.fit_info()

    # Do prediction
    y_test_pred = model_fitter.predict(x_test)
    if predict_training:
        y_train_pred = model_fitter.predict(x_train)

    # Internally update the model results in the ModelData object
    model_data.update_test_df_with_preds(y_test_pred)

    # Write the model results to the database
    if update:
        model_data.update_remote_tables()

    # Write the model results to file
    if write_prediction:
        if results_dir is None:
            test_pred_filepath = os.path.join(kwargs["config_dir"], "test_pred.pickle")
            train_pred_filepath = os.path.join(
                kwargs["config_dir"], "train_pred.pickle"
            )
        else:
            test_pred_filepath = os.path.join(results_dir, "test_pred.pickle")
            train_pred_filepath = os.path.join(results_dir, "train_pred.pickle")
        with open(test_pred_filepath, "wb") as results_file:
            pickle.dump(y_test_pred, results_file)
        if predict_training:
            with open(train_pred_filepath, "wb") as results_file:
                pickle.dump(y_train_pred, results_file)


if __name__ == "__main__":
    main()
