"""
Model fitting
"""
import logging
import argparse
# from dateutil.parser import isoparse
# from dateutil.relativedelta import relativedelta
from cleanair.models import TrafficForecast
from cleanair.loggers import get_log_level


def main():
    """
    Predict SCOOT forecast
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Forecast SCOOT readings")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        default="now",
        help="The last datetime (YYYY-MM-DD HH:MM:SS) to get data for.",
    )
    parser.add_argument(
        "-n",
        "--ndays",
        type=int,
        default=7,
        help="The number of days to request data for.",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()
    if args.ndays < 1:
        raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # # Get training and pred start and end datetimes
    # train_end = kwargs.pop("trainend")
    # train_n_hours = kwargs.pop("trainhours")
    # pred_start = kwargs.pop("predstart")
    # pred_n_hours = kwargs.pop("predhours")
    # train_start = strtime_offset(train_end, -train_n_hours)
    # pred_end = strtime_offset(pred_start, pred_n_hours)

    # # Model configuration
    # model_config = {
    #     "train_start_date": train_start,
    #     "train_end_date": train_end,
    #     "pred_start_date": pred_start,
    #     "pred_end_date": pred_end,
    #     "include_satellite": True,
    #     "include_prediction_y": False,
    #     "train_sources": ["laqn", "aqe"],
    #     "pred_sources": ["grid_100"],
    #     "train_interest_points": "all",
    #     "train_satellite_interest_points": "all",
    #     "pred_interest_points": "all",
    #     "species": ["NO2"],
    #     "features": [
    #         "value_1000_total_a_road_length",
    #         "value_500_total_a_road_length",
    #         "value_500_total_a_road_primary_length",
    #         "value_500_total_b_road_length",
    #     ],
    #     "norm_by": "laqn",
    #     "model_type": "svgp",
    #     "tag": "test_grid",
    # }

    # # Model fitting parameters
    # model_params = {
    #     "lengthscale": 0.1,
    #     "variance": 0.1,
    #     "minibatch_size": 100,
    #     "n_inducing_points": 2000,
    # }

    # Perform update and notify any exceptions
    try:
        scoot_forecaster = TrafficForecast(**kwargs)
        scoot_forecaster.forecast()
        scoot_forecaster.update_remote_tables()

        # TrafficForecast

        # # Check that we have AWS connection information and try to retrieve it from a local secrets file if not
        # if not (args.aws_key_id and args.aws_key):
        #     try:
        #         with open(os.path.join("/secrets", "aws_secrets.json")) as f_secret:
        #             data = json.load(f_secret)
        #             args.aws_key_id = data["aws_key_id"]
        #             args.aws_key = data["aws_key"]
        #     except json.decoder.JSONDecodeError:
        #         raise argparse.ArgumentTypeError(
        #             "Could not determine SCOOT aws_key_id or aws_key"
        #         )

        # # Update the Scoot readings table on the database
        # scoot_writer = ScootWriter(**kwargs)
        # scoot_writer.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
