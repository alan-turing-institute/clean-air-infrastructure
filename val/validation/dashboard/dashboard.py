"""
The main plotly dashboard.

Inspired by https://dash.plot.ly/interactive-graphing

"""

from . import timeseries
from . import layout
from .. import util, metrics

def main(exp):
    # get the model data object and create metrics
    model_data = exp.get_model_data_list()[0]
    scores_df = metrics.measure_scores_by_sensor(
        model_data.normalised_training_data_df, metrics.get_metric_methods()
    )
    point_df = metrics.concat_static_features_with_scores(
        scores_df, model_data.normalised_training_data_df
    )

    # create the base layout
    app = layout.get_base_layout(point_df)
    print("Served at: http://127.0.0.1:8050")
    app.run_server(debug=True)

if __name__ == "__main__":
    main()
