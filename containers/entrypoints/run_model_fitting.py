"""
Model fitting
"""
import logging
import argparse
from datetime import datetime
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
import numpy as np
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
    parser.add_argument("-v", "--verbose", action="count", default=0)

    parser.add_argument(
        "--trainend",
        type=str,
        default="2020-01-10T00:00:00",
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
        default="2020-01-10T00:00:00",
        help="The first datetime (YYYY-MM-DD HH:MM:SS) to get model data for prediction.",
    )
    parser.add_argument(
        "--predhours", type=int, default=48, help="The number of hours to predict for"
    )
    parser.add_argument(
        "-t",
        "--testdir",
        default="/secrets/test/",
        type=str,
        help="The directory to save test data.",
    )
    parser.add_argument(
        "-w", "--write", action="store_true", help="Write model data to file."
    )
    parser.add_argument(
        "-r", "--read", action="store_true", help="Read model data from file."
    )

    # Parse and interpret arguments
    args = parser.parse_args()
    testdir = args.testdir
    write = args.write
    read = args.read
    kwargs = vars(args)
    del kwargs["testdir"]
    del kwargs["write"]
    del kwargs["read"]

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

    # initialise the model
    model_fitter = SVGP_TF1()

    # Get the model data
    if read:
        model_data = ModelData(config_dir=testdir, **kwargs)
    else:
        model_data = ModelData(config=model_config, **kwargs)

    if write:
        print(testdir)
        model_data.save_config_state(testdir)

    # get the training and test dictionaries
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=True)
    x_train = training_data_dict['X']
    y_train = training_data_dict['Y']
    x_test = predict_data_dict['X']

    # Fit the model
    model_fitter.fit(
        x_train,
        y_train,
        save_model_state=False,
        max_iter=5,
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

    print(model_data.normalised_pred_data_df.sample(5))

    # Write the model results to the database
    # model_data.update_remote_tables()

    return model_data

if __name__ == "__main__":
    main()
