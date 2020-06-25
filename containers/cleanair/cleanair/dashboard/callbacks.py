"""
Function to handle callbacks from apps.
"""
from . import timeseries


def ip_timeseries_callback(hover_data, point_groupby, pollutant="NO2"):
    """
    When hovering over a point, update the timeseries showing the prediction.
    """
    point_id = hover_data["points"][0]["hovertext"]
    point_df = point_groupby.get_group(point_id)
    return dict(
        data=timeseries.timeseries_prediction_trace(
            point_df["measurement_start_utc"],
            point_df[pollutant],
            point_df[pollutant + "_mean"],
            point_df[pollutant + "_var"],
            line_name=pollutant + " prediction",
            marker_name=pollutant + " observations",
        ),
        layout=dict(title="Prediction for point {id}".format(id=point_id)),
    )


def interest_point_mapbox_callback(mapbox_fig, sensor_scores_df, metric_key, pollutant):
    """
    Update the map of sensors when a different pollutant or metric is chosen.
    """
    mapbox_fig.update_layout(
        coloraxis_colorbar=dict(title=pollutant + " " + metric_key)
    )
    return mapbox_fig.update_traces(
        dict(marker=dict(color=sensor_scores_df[pollutant + "_" + metric_key]))
    )
