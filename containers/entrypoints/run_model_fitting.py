"""
Model fitting
"""
import logging
import argparse
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from cleanair.models import ModelData, ModelFitting
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

    parser.add_argument("--trainend", type=str, default='2019-11-01T00:00:00',
                        help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for training.")
    parser.add_argument("--trainhours", type=int, default=168,
                        help="The number of hours to get training data for.")
    parser.add_argument("--predstart", type=str, default='2019-11-01T00:00:00',
                        help="The first datetime (YYYY-MM-DD HH:MM:SS) to get model data for prediction.")
    parser.add_argument("--predhours", type=int, default=48,
                        help="The number of hours to predict for")

    # Parse and interpret arguments
    args = parser.parse_args()
    kwargs = vars(args)

    # Set logging verbosity
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # Get training and test start and end datetimes
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

                    'train_sources': ['laqn', 'aqe'],
                    'pred_sources': ['laqn', 'aqe'],
                    'species': ['NO2'],
                    'features': 'all',
                    'norm_by': 'laqn',
                    'model_type': 'svgp',
                    'tag': 'production'}

    # Get the model data
    model_data = ModelData(**kwargs)
    model_data.initialise(config=model_config)

    training_data_dict = model_data.get_training_data_arrays(dropna=False)
    print(training_data_dict)
    predict_data_dict = model_data.get_test_data_arrays(dropna=False)
    print(predict_data_dict)
    # # Fit the model
    # model_fitter = ModelFitting()

    # model_fitter.fit(training_data_dict['X'],
    #                  training_data_dict['Y'],
    #                  max_iter=20000,
    #                  model_params=dict(lengthscales=0.1,
    #                                    variance=0.1,
    #                                    minibatch_size=100,
    #                                    n_inducing_points=3000))

    # # # # Do prediction and write to database
    # predict_df = model_fitter.predict(predict_data_dict['X'])
    # model_data.update_model_results_table(data_df=predict_df)


if __name__ == "__main__":
    main()
