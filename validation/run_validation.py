import sys
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta

sys.path.append("../containers")

from cleanair.models import ModelData, SVGP

def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()

def forecast():
    """
    Forecast air quality.
    """
    pass

def rolling_forecast():
    """
    Train and predict for multiple time periods in a row.
    """
    pass

if __name__ == "__main__":
    # Set dates for training and testing
    train_end = "2019-11-01T23:00:00"
    train_n_hours = 24
    pred_n_hours = 12
    pred_start = "2019-11-02T00:00:00"
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
                    'features': ['value_1000_building_height'],
                    'norm_by': 'laqn',
                    'model_type': 'svgp',
                    'tag': 'testing'}

    # Model fitting parameters
    model_params = {'lengthscale': 0.1,
                    'variance': 0.1,
                    'minibatch_size': 100,
                    'n_inducing_points': 3000}

    # Get the model data
    model_data = ModelData()
    model_data.initialise(config=model_config)

    # training_data_dict = model_data.training_data_df
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_test_data_arrays(dropna=False)

    # Fit the model
    model_fitter = SVGP()

    model_fitter.fit(training_data_dict['X'],
                     training_data_dict['Y'],
                     max_iter=5,
                     model_params=model_params)

    # Get info about the model fit
    model_fit_info = model_fitter.fit_info()

    # Do prediction and write to database
    Y_pred = model_fitter.predict(predict_data_dict['X'])

    # Write the model results to the database
    model_data.update_model_results_table(
        predict_data_dict=predict_data_dict,
        Y_pred=Y_pred,
        model_fit_info=model_fit_info
    )