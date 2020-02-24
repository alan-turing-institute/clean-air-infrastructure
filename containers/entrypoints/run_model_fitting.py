"""
Model fitting
"""
import os
import logging
import pickle
from datetime import datetime
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from cleanair.models import ModelData, SVGP
from cleanair.loggers import get_log_level
from cleanair.parsers import ModelFitParser


def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()


def write_predictions_to_file(y_pred, results_dir, filename):
    """Write a prediction dict to pickle."""
    pred_filepath = os.path.join(results_dir, filename)
    with open(pred_filepath, "wb") as handle:
        pickle.dump(y_pred, handle)


def get_train_test_start_end(kwargs):
    """
    Given kwargs return dates for training and testing.
    """
    train_end = kwargs.pop("trainend")
    train_n_hours = kwargs.pop("trainhours")
    pred_start = kwargs.pop("predstart")
    pred_n_hours = kwargs.pop("predhours")
    train_start = strtime_offset(train_end, -train_n_hours)
    pred_end = strtime_offset(pred_start, pred_n_hours)
    return train_start, train_end, pred_start, pred_end


def get_data_config(kwargs):
    """
    Return a dictionary of model data configs given parser arguments.
    """
    # Get training and pred start and end datetimes
    train_start, train_end, pred_start, pred_end = get_train_test_start_end(kwargs)
    return_y = kwargs.pop("return_y")
    tag = kwargs.pop("tag")

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
        "tag": tag,
    }
    return model_config


def main():  # pylint: disable=R0914
    """
    Run model fitting
    """
    # Read command line arguments
    parser = ModelFitParser(description="Run model fitting")

    # Parse and interpret arguments
    kwargs = parser.parse_kwargs()

    # Update database/write to file
    no_db_write = kwargs.pop("no_db_write")
    local_write = kwargs.pop("local_write")
    local_read = kwargs.pop("local_read")
    predict_write = kwargs.pop("predict_write")
    results_dir = kwargs.pop("results_dir")
    model_dir = kwargs.pop("model_dir")
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
    model_fitter.model_params["maxiter"] = 10
    model_fitter.model_params["model_state_fp"] = model_dir

    # Get the model data
    if local_read:
        logging.info("Reading local data")
        model_data = ModelData(**kwargs)
    else:
        model_data = ModelData(config=model_config, **kwargs)

    # write model results to file
    if local_write:
        model_data.save_config_state(kwargs["config_dir"])

    # get the training and test dictionaries
    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False)
    x_train = training_data_dict["X"]
    y_train = training_data_dict["Y"]
    x_test = predict_data_dict["X"]

    # Fit the model
    logging.info(
        "Training the model for %s iterations.", model_fitter.model_params["maxiter"]
    )
    fit_start_time = datetime.now()
    model_fitter.fit(x_train, y_train)

    # Get info about the model fit
    # model_fit_info = model_fitter.fit_info()

    # Do prediction
    y_test_pred = model_fitter.predict(x_test)
    if predict_training:
        x_train_pred = x_train.copy()
        if "satellite" in x_train:
            x_train_pred.pop("satellite")
        y_train_pred = model_fitter.predict(x_train_pred)

    # Internally update the model results in the ModelData object
    model_data.update_test_df_with_preds(y_test_pred, fit_start_time)

    # Write the model results to the database
    if not no_db_write:
        # see issue 103: generalise for multiple pollutants
        model_data.normalised_pred_data_df[
            "predict_mean"
        ] = model_data.normalised_pred_data_df["NO2_mean"]
        model_data.normalised_pred_data_df[
            "predict_var"
        ] = model_data.normalised_pred_data_df["NO2_var"]
        model_data.update_remote_tables()

    # Write the model results to file
    if predict_write:
        write_predictions_to_file(y_test_pred, results_dir, "test_pred.pickle")
        if predict_training:
            write_predictions_to_file(y_train_pred, results_dir, "train_pred.pickle")


if __name__ == "__main__":
    main()
