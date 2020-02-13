"""
Model fitting
"""
import logging
import argparse
from datetime import datetime
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
import numpy as np
from cleanair.models import ModelData, SVGP
from cleanair.loggers import get_log_level


def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()


def main():
    """
    Run model fitting
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Run model fitting")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="../../terraform/.secrets/db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument(
        "-d",
        "--config_dir",
        default="./",
        help="Filepath to directory to store model and data.",
    )
    parser.add_argument(
        "-w", "--write", action="store_true", help="Write model data config to file.",
    )
    parser.add_argument(
        "-r", "--read", action="store_true", help="Read model data from config_dir.",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update the database with model results.",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    parser.add_argument(
        "--trainend",
        type=str,
        default="2020-01-30T00:00:00",
        help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for training.",
    )
    parser.add_argument(
        "--trainhours",
        type=int,
        default=48,
        help="The number of hours to get training data for.",
    )
    parser.add_argument(
        "--predstart",
        type=str,
        default="2020-01-30T00:00:00",
        help="The first datetime (YYYY-MM-DD HH:MM:SS) to get model data for prediction.",
    )
    parser.add_argument(
        "--predhours", type=int, default=48, help="The number of hours to predict for"
    )

    # Parse and interpret arguments
    args = parser.parse_args()
    kwargs = vars(args)

    # Update database/write to file
    update = kwargs.pop("update")
    write = kwargs.pop("write")
    read = kwargs.pop("read")

    # Set logging verbosity
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # Get training and pred start and end datetimes
    train_end = kwargs.pop("trainend")
    train_n_hours = kwargs.pop("trainhours")
    pred_start = kwargs.pop("predstart")
    pred_n_hours = kwargs.pop("predhours")
    train_start = strtime_offset(train_end, -train_n_hours)
    pred_end = strtime_offset(pred_start, pred_n_hours)

    # Model configuration
    model_config = {
        "train_start_date": train_start,
        "train_end_date": train_end,
        "pred_start_date": pred_start,
        "pred_end_date": pred_end,
        "include_satellite": False,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        "pred_sources": ["laqn", "hexgrid"],
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
        "tag": "tf1_test",
    }

    if "aqe" in model_config["train_sources"] + model_config["pred_sources"]:
        raise NotImplementedError("AQE cannot currently be run. Coming soon")

    if model_config["species"] != ["NO2"]:
        raise NotImplementedError(
            "The only pollutant we can model right now is NO2. Coming soon"
        )

    # initialise the model
    model_fitter = SVGP(batch_size=1000)  # big batch size for the grid
    model_fitter.model_params["maxiter"] = 1
    model_fitter.model_params["model_state_fp"] = args.config_dir

    # Get the model data
    if read:
        model_data = ModelData(**kwargs)
    else:
        model_data = ModelData(config=model_config, **kwargs)

    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False)

    # the shapes of the arrays
    y_train_shape = training_data_dict["Y"].shape

    # get the training and testing data into the correct format
    x_train = dict(laqn=training_data_dict["X"])
    y_train = dict(
        laqn=dict(NO2=np.reshape(training_data_dict["Y"], (y_train_shape[0], 1)))
    )
    x_test = dict(laqn=predict_data_dict["X"])

    # Fit the model
    model_fitter.fit(x_train, y_train, save_model_state=False)

    # Get info about the model fit
    # model_fit_info = model_fitter.fit_info()

    # Do prediction and write to database
    y_pred = model_fitter.predict(x_test)

    # Internally update the model results in the ModelData object
    model_data.update_model_results_df(
        predict_data_dict=predict_data_dict,
        Y_pred=np.array(
            [y_pred["laqn"]["NO2"]["mean"], y_pred["laqn"]["NO2"]["var"]]
        ).T.squeeze(),
        model_fit_info=dict(fit_start_time=datetime.now()),
    )
    # write model results to file
    if write:
        model_data.save_config_state(args.config_dir)

    # Write the model results to the database
    if update:
        model_data.update_remote_tables()


if __name__ == "__main__":
    main()
