"""
Plotly figures for timeseries data.
"""

def get_pollutant_point_trace(point_pred_df, col='NO2_mean', name=None):
    """
    Return a plotly trace dict for a timeseries of the mean prediction on a sensor.
    """
    name = col if name == None else name
    return dict(
        x=list(point_pred_df['measurement_start_utc']),
        y=list(point_pred_df[col]),
        mode='lines',
        name=name
    )