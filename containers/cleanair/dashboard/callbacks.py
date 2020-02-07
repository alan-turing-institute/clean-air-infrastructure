from . import timeseries
from . import geomap

def interest_point_timeseries_callback(hover_data, point_groupby, pollutant='NO2'):
    """
    When hovering over a point, update the timeseries showing the prediction.
    """
    print(hover_data)
    point_id = hover_data['points'][0]['hovertext']
    point_pred_df = point_groupby.get_group(point_id)
    mean_trace = timeseries.get_pollutant_point_trace(point_pred_df, col=pollutant + '_mean')
    actual_trace = timeseries.get_pollutant_point_trace(point_pred_df, col=pollutant)
    return dict(
        data=[mean_trace, actual_trace],
        layout=dict(
            title='Prediction for point {id}'.format(id=point_id)
        )
    )

def interest_point_map_callback(mapbox_fig, sensor_scores_df, metric_key, pollutant):
    """
    Update the map of sensors when a different pollutant or metric is chosen.
    """
    pass
