"""
Meta components that make up the dashboard.
"""

import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px
from . import timeseries
from ..metrics.evaluate import pop_kwarg

METRIC_NAMES = {
    "mae": "Mean absolute error",
    "mse": "Mean squared error",
    "r2_score": "R squared score",
}
POLLUTANT_NAMES = dict(
    NO2="Nitrogen Dioxide",
    O3="Ozone",
    CO2="Carbon Dioxide",
    PM10="Particulate Matter (10 micro m)",
    PM25="Particulate Matter (2.5 micro m)",
)


class ModelFitComponent:
    """
    Collect all the components of a model fit and its layout in the app.
    """

    def __init__(
        self, instance_id, model_data, sensor_scores_df, temporal_scores_df, **kwargs,
    ):
        """
        Initialise with a model data object and the scores for the fit.
        """
        self.instance_id = instance_id
        self.model_data = model_data
        self.sensor_scores_df = sensor_scores_df
        self.temporal_scores_df = temporal_scores_df
        self.evaluate_training = pop_kwarg(kwargs, "evaluate_training", False)
        self.evaluate_testing = pop_kwarg(kwargs, "evaluate_testing", True)
        self.interest_points_map_id = pop_kwarg(
            kwargs, "interest_points_map_id", "interest-points-map"
        )
        self.interest_points_timeseries_id = pop_kwarg(
            kwargs, "interest_points_timeseries_id", "interest-points-timeseries"
        )
        self.temporal_metrics_timeseries_id = pop_kwarg(
            kwargs, "temporal_metrics_timeseries_id", "temporal_metrics_timeseries"
        )
        # execute and store the group bys
        if self.evaluate_training and self.evaluate_testing:
            # ToDo: test eval training and testing works
            # append train and test dfs then group by point id
            self.point_groupby = self.model_data.normalised_training_data_df.append(
                self.model_data.normalised_pred_data_df, ignore_index=True
            ).groupby("point_id")
        elif self.evaluate_training:
            # only groupby on training set
            self.point_groupby = self.model_data.normalised_training_data_df.groupby(
                "point_id"
            )
        elif self.evaluate_testing:
            # only groupby on test set
            self.point_groupby = self.model_data.normalised_pred_data_df.groupby(
                "point_id"
            )
        else:
            raise ValueError(
                "Must set either evaluate_training or evauluate_testing (or both) to True."
            )

    def get_interest_points_map(self, metric_key, pollutant):
        """
        Get a map with interest points plotted and the colour of points is the metric score.
        """
        return px.scatter_mapbox(
            self.sensor_scores_df,
            lat="lat",
            lon="lon",
            size=[15 for i in range(len(list(self.sensor_scores_df.index)))],
            color=pollutant + "_" + metric_key,
            zoom=10,
            mapbox_style="basic",
            hover_name=self.sensor_scores_df["point_id"],
        )

    def get_interest_points_timeseries(self, point_id, pollutant):
        """
        Get a map with interest points plotted.
        """
        return dcc.Graph(
            id=self.interest_points_timeseries_id,
            figure=go.Figure(
                data=[
                    timeseries.get_pollutant_point_trace(
                        self.point_groupby.get_group(point_id), col=pollutant
                    ),
                    timeseries.get_pollutant_point_trace(
                        self.point_groupby.get_group(point_id), col=pollutant + "_mean"
                    ),
                ],
                layout=dict(title="Prediction for point {id}".format(id=point_id)),
            ),
        )

    def get_temporal_metrics_timeseries(self, metric_key, pollutant):
        """
        Get a timeseries of the score for a given metric over the prediction period.
        """
        col = pollutant + "_" + metric_key
        name = METRIC_NAMES[metric_key]
        return dict(
            data=[
                dict(
                    x=list(self.temporal_scores_df["measurement_start_utc"]),
                    y=list(self.temporal_scores_df[col]),
                    mode="lines",
                    name=name,
                )
            ],
            layout=dict(
                title="{mtc} score for all sensors over time.".format(
                    mtc=METRIC_NAMES[metric_key]
                )
            ),
        )


def get_model_data_fit_intro():
    """
    Get the markdown for the introduction text for a model fit.
    """
    introduction = """
        #### Showing the errors on sensors in space

        Each dot in the diagram below shows a sensor.
        The colour of a sensor is the error on that sensor.
        When you hover over a sensor, the timeseries will show the predictive mean, variance and actual reading of the sensor.
    """
    return dcc.Markdown(introduction)


def get_pollutant_dropdown(component_id, species):
    """
    Get a dropdown menu with all possible pollutants inside.
    """
    return dcc.Dropdown(
        id=component_id,
        className="col-6",
        options=[
            dict(label=POLLUTANT_NAMES[pollutant], value=pollutant)
            for pollutant in species
        ],
        value=species[0],
    )


def get_metric_dropdown(component_id, metric_keys):
    """
    Get a dropdown menu with all available metrics.
    """
    return dcc.Dropdown(
        id=component_id,
        className="col-6",
        options=[dict(label=METRIC_NAMES[key], value=key) for key in metric_keys],
        value=metric_keys[0],
    )
