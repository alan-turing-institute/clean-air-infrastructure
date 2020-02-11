"""
Model fitting
"""
import logging
import argparse
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from cleanair.models import ModelData, SVGP_TF1
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
        default="db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument(
        "-d",
        "--config_dir",
        default="./",
        help="Filepath to directory to store model and data."
    )
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="Write model data config to file.",
    )
    parser.add_argument(
        "-r",
        "--read",
        action="store_true",
        help="Read model data from config_dir.",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update the database with model results.",
    )
    parser.add_argument(
        "-y",
        "--return_y",
        action="store_true",
        help="Include pollutant data in the test dataset.",
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
    return_y = kwargs.pop("return_y")

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
        "model_type": "svgp_tf1",
        "tag": "testing_dashboard",
    }

    if 'aqe' in model_config['train_sources'] + model_config['pred_sources']:
        NotImplementedError("AQE cannot currently be run. Coming soon")

    if model_config['species'] != ['NO2']:
        NotImplementedError("The only pollutant we can model right now is NO2. Coming soon")

    # initialise the model
    model_fitter = SVGP_TF1(batch_size=100)   # big batch size for the grid
    model_fitter.model_params["maxiter"] = 100
    model_fitter.model_params["model_state_fp"] = args.config_dir

    # Get the model data
    if read:
        model_data = ModelData(**kwargs)
    else:
        model_data = ModelData(config=model_config, **kwargs)

    # write model results to file
    if write:
        model_data.save_config_state(args.config_dir)

    # get the training and test dictionaries
    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False)
    x_train = training_data_dict['X']
    y_train = training_data_dict['Y']
    x_test = predict_data_dict['X']

    # Fit the model
    model_fitter.fit(
        x_train,
        y_train,
        save_model_state=False
    )

    # Get info about the model fit
    # model_fit_info = model_fitter.fit_info()

    # Do prediction and write to database
    y_pred = model_fitter.predict(x_test)

    try:
        num_pred_rows = y_pred['laqn']['NO2']['mean'].shape[0]
        num_x_rows = x_test['laqn'].shape[0]
        assert num_pred_rows == num_x_rows
    except AssertionError:
        error_message = 'Rows in y_pred laqn No2 mean is {pred_rows}. '.format(
            pred_rows=num_pred_rows
        )
        error_message += 'Rows in x_test laqn is {x_rows}. '.format(
            x_rows=num_x_rows
        )
        error_message += 'The number of rows in both arrays should be the same.'
        raise ValueError(error_message)

    # Internally update the model results in the ModelData object
    model_data.update_test_df_with_preds(y_pred)

    # Write the model results to the database
    if update:
        model_data.update_remote_tables()

    return model_data

if __name__ == "__main__":
    main()
