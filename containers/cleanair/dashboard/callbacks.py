from . import timeseries

def interest_point_map_callback(hover_data, point_groupby):
    point_id = hover_data['points'][0]['hovertext']
    point_pred_df = point_groupby.get_group(point_id)
    mean_trace = timeseries.get_pollutant_point_trace(point_pred_df)
    actual_trace = timeseries.get_pollutant_point_trace(point_pred_df, col='NO2')
    return dict(
        data=[mean_trace, actual_trace],
        layout=dict(
            title='Prediction for point {id}'.format(id=point_id)
        )
    )
