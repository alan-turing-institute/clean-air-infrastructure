"""
Temporal validation methods.
"""

import sys
from metrics import get_metric_methods, measure_scores_by_hour
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta

sys.path.append("../containers")
from cleanair.models import SVGP

def forecast(model_fitter, model_data, model_params={}, max_iter=1000, return_results=False):
    """
    Forecast air quality.

    Parameters
    ___

    model_fitter : SVGP
        Model fitter object.

    model_data : ModelData
        Initialised model data object.

    model_params : dict
        Model parameters and settings.

    max_iter : int
        ToDo

    Returns
    ___

    scores : DataFrame
        Contains the validation scores for each hour of the forecast.

    """

    # get training and testing data
    model_data.normalised_training_data_df.to_csv('results/normalised_df.csv')
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=True, return_y=True)
    x_test, y_test = predict_data_dict['X'], predict_data_dict['Y']

    # fit the model
    model_fitter.fit(training_data_dict['X'],
                    training_data_dict['Y'],
                    max_iter=max_iter,
                    model_params=model_params)

    # Get info about the model fit
    model_fit_info = model_fitter.fit_info()

    # Do prediction
    print("X test shape:", x_test.shape)
    print("Y test shape:", y_test.shape)
    pred = model_fitter.predict(x_test)

    # Write the model results to dataframe
    model_data.update_model_results_df(
        predict_data_dict=predict_data_dict,
        Y_pred=pred,
        model_fit_info=model_fit_info
    )
    
    # filter out nans
    print()
    print("### columns:")
    print(list(model_data.normalised_pred_data_df.columns))
    # useful_df = model_data.normalised_pred_data_df[[
    #     'measurement_start_utc', 'point_id', 'source', 'location',
    #     'lat', 'lon', 'fit_start_time', 'predict_mean', 'predict_var'
    # ] + model_data.y_names]
    useful_df = model_data.normalised_pred_data_df[[
        'measurement_start_utc', 'point_id', 'source',
        'lat', 'lon', 'fit_start_time', 'predict_mean', 'predict_var'
    ] + model_data.y_names]

    pred_data_df = model_data.normalised_pred_data_df.copy()[['measurement_start_utc', 'predict_mean'] + model_data.y_names].dropna()
    
    # calculate scores for each metric for each hour over all sensors
    metric_methods = get_metric_methods()
    scores = measure_scores_by_hour(pred_data_df, metric_methods)

    if return_results:
        return scores, useful_df
    return scores

def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()

def create_rolls(train_start, train_n_hours, pred_n_hours, num_rolls):
    """Create a list of dictionaries with train and pred dates rolled up."""
    start_of_roll = train_start
    rolls = []

    for i in range(num_rolls):

        train_end = strtime_offset(start_of_roll, train_n_hours)
        pred_start = strtime_offset(start_of_roll, train_n_hours)
        pred_end = strtime_offset(pred_start, pred_n_hours)
        rolls.append({
            'train_start_date': start_of_roll,
            'train_end_date': train_end,
            'pred_start_date': pred_start,
            'pred_end_date': pred_end
        })
        start_of_roll = strtime_offset(start_of_roll, pred_n_hours)
    
    return rolls

def rolling_forecast(model_name, model_data_list, model_params={}, max_iter=1000, return_results=False):
    """
    Train and predict for multiple time periods in a row.
    """
    models = {
        "svgp":SVGP
    }
    roll = 0
    for model_data in model_data_list:
        print()
        print("iteration", roll)
        model_fitter = models[model_name]()
        if return_results:
            scores_df, pred_df = forecast(model_fitter, model_data, model_params=model_params, max_iter=max_iter, return_results=True)
        else:
            scores_df = forecast(model_fitter, model_data, model_params=model_params, max_iter=max_iter)
        
        # update all_preds if return_results is true
        if roll == 0 and return_results:
            all_preds_df = pred_df.copy()
        elif roll > 0 and return_results:
            all_preds_df = all_preds_df.append(pred_df)

        # update the metric results df
        if roll == 0:
            results_df = scores_df.copy()
        else:
            results_df = results_df.append(scores_df)
        roll += 1

    if return_results:
        return results_df, all_preds_df
    return results_df
