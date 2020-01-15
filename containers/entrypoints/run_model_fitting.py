"""
Model fitting
"""
import logging
import argparse
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
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
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    parser.add_argument("--trainend", type=str, default='2019-11-10T00:00:00',
                        help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for training.")
    parser.add_argument("--trainhours", type=int, default=48,
                        help="The number of hours to get training data for.")
    parser.add_argument("--predstart", type=str, default='2019-11-10T00:00:00',
                        help="The first datetime (YYYY-MM-DD HH:MM:SS) to get model data for prediction.")
    parser.add_argument("--predhours", type=int, default=48,
                        help="The number of hours to predict for")

    # Parse and interpret arguments
    args = parser.parse_args()
    kwargs = vars(args)

    # Set logging verbosity
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # Get training and pred start and end datetimes
    train_end = kwargs.pop('trainend')
    train_n_hours = kwargs.pop('trainhours')
    pred_start = kwargs.pop('predstart')
    pred_n_hours = kwargs.pop('predhours')
    train_start = strtime_offset(train_end, -train_n_hours)
    pred_end = strtime_offset(pred_start, pred_n_hours)

    # Model configuration
    model_config = {'train_start_date': train_start,
                    'train_end_date': train_end,
                    'pred_start_date': pred_start,
                    'pred_end_date': pred_end,

                    'include_satellite': False,
                    'include_prediction_y': False,
                    'train_sources': ['laqn', 'aqe'],
                    'pred_sources': ['laqn', 'aqe'],
                    'train_interest_points': 'all',
                    'train_satellite_interest_points': 'all',
                    'pred_interest_points': 'all',
                    'species': ['NO2'],
                    "features": [
                        "value_1000_avg_min_width",
                        "value_1000_avg_ratio_avg",
                        "value_1000_building_height",
                        "value_1000_flat",
                        "value_1000_grass",
                        "value_1000_hospitals",
                        "value_1000_max_min_width",
                        "value_1000_max_ratio_avg",
                        "value_1000_min_ratio_avg",
                        "value_1000_museums",
                        "value_1000_park",
                        "value_1000_total_a_road_length",
                        "value_1000_total_a_road_primary_length",
                        "value_1000_total_b_road_length",
                        "value_1000_total_length",
                        "value_1000_total_road_length",
                        "value_1000_water",
                        "value_500_avg_min_width",
                        "value_500_avg_ratio_avg",
                        "value_500_building_height",
                        "value_500_flat",
                        "value_500_grass",
                        "value_500_hospitals",
                        "value_500_max_min_width",
                        "value_500_max_ratio_avg",
                        "value_500_min_min_width",
                        "value_500_min_ratio_avg",
                        "value_500_museums",
                        "value_500_park",
                        "value_500_total_a_road_length",
                        "value_500_total_a_road_primary_length",
                        "value_500_total_b_road_length",
                        "value_500_total_length",
                        "value_500_total_road_length",
                        "value_500_water",
                        "value_200_avg_min_width",
                        "value_200_avg_ratio_avg",
                        "value_200_building_height",
                        "value_200_flat",
                        "value_200_grass",
                        "value_200_hospitals",
                        "value_200_max_min_width",
                        "value_200_max_ratio_avg",
                        "value_200_min_min_width",
                        "value_200_min_ratio_avg",
                        "value_200_museums",
                        "value_200_park",
                        "value_200_total_a_road_length",
                        "value_200_total_a_road_primary_length",
                        "value_200_total_b_road_length",
                        "value_200_total_length",
                        "value_200_total_road_length",
                        "value_200_water",
                        "value_100_avg_min_width",
                        "value_100_avg_ratio_avg",
                        "value_100_building_height",
                        "value_100_flat",
                        "value_100_grass",
                        "value_100_hospitals",
                        "value_100_max_min_width",
                        "value_100_max_ratio_avg",
                        "value_100_min_min_width",
                        "value_100_min_ratio_avg",
                        "value_100_museums",
                        "value_100_park",
                        "value_100_total_a_road_length",
                        "value_100_total_a_road_primary_length",
                        "value_100_total_b_road_length",
                        "value_100_total_length",
                        "value_100_total_road_length",
                        "value_100_water",
                        "value_10_avg_min_width",
                        "value_10_avg_ratio_avg",
                        "value_10_building_height",
                        "value_10_flat",
                        "value_10_grass",
                        "value_10_max_min_width",
                        "value_10_max_ratio_avg",
                        "value_10_min_min_width",
                        "value_10_min_ratio_avg",
                        "value_10_park",
                        "value_10_total_a_road_length",
                        "value_10_total_a_road_primary_length",
                        "value_10_total_b_road_length",
                        "value_10_total_length",
                        "value_10_total_road_length",
                        "value_10_water"
                    ],
                    'norm_by': 'laqn',
                    'model_type': 'svgp',
                    'tag': 'testing'}

    # Model fitting parameters
    model_params = {'lengthscale': 0.1,
                    'variance': 0.1,
                    'minibatch_size': 100,
                    'n_inducing_points': 2000}

    # Get the model data
    model_data = ModelData(config=model_config, **kwargs)

    model_data.save_config_state('/secrets/test/')

    # print(model_data.get_satellite_forecast(train_start, train_end))

    # # training_data_dict = model_data.training_data_df
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False)

    # print(training_data_dict['X_train'])
    # print(training_data_dict['Y_train'])
    # print(training_data_dict['Y_sat'])

    # Fit the model
    model_fitter = SVGP()

    model_fitter.fit(training_data_dict['X'],
                     training_data_dict['Y'],
                     max_iter=20000,
                     model_params=model_params)

    # Get info about the model fit
    model_fit_info = model_fitter.fit_info()

    # # Do prediction and write to database
    Y_pred = model_fitter.predict(predict_data_dict['X'])

    # Internally update the model results in the ModelData object
    model_data.update_model_results_df(predict_data_dict=predict_data_dict,
                                       Y_pred=Y_pred,
                                       model_fit_info=model_fit_info)

    # Write the model results to the database
    model_data.update_remote_tables()


if __name__ == "__main__":
    main()
