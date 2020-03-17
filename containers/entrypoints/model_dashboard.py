"""
Visualise and run metrics for a single model data fit.
"""
import os
import json
import logging
import pandas as pd
from cleanair import metrics
from cleanair.dashboard import apps
from cleanair.instance import ProductionInstance, ValidationInstance
from cleanair.parsers import DashboardParser


def main():  # pylint: disable=too-many-locals
    """
    Run the model fitting entrypoint and show the scores in a plotly dashboard.
    """
    evaluate_training = False   # ToDo: extend dashboard for training set.

    # parse command line arguments
    parser = DashboardParser(description="Dashboard")
    kwargs = parser.parse_all()
    xp_config = parser.experiment_args
    secrets_dir = os.path.dirname(xp_config["secretfile"])

    # all possible instances
    tag_to_instance = dict(
        production=ProductionInstance,
        validation=ValidationInstance,
    )
    # the instance class from a tag
    instance_class = tag_to_instance[kwargs.get("tag")]

    # get experiment config
    experiment_config = instance_class.DEFAULT_EXPERIMENT_CONFIG
    experiment_config.update(xp_config)

    # load the instance
    instance_id = kwargs.pop("instance_id")
    instance = instance_class.instance_from_id(instance_id, experiment_config, **kwargs)
    assert instance.instance_id == instance_id

    # get the data and the results
    print(json.dumps(instance.convert_dates_to_str(), indent=4))
    instance.load_data()
    assert instance.instance_id == instance_id
    results_df = instance.load_results()
    instance.model_data.normalised_pred_data_df = pd.merge(
        instance.model_data.normalised_pred_data_df,
        results_df,
        how="inner",
        on=["point_id", "measurement_start_utc"],
    )

    # get the mapbox api key
    try:
        mapbox_filepath = os.path.join(secrets_dir, ".mapbox_token")
        mapbox_access_token = open(mapbox_filepath).read()
    except FileNotFoundError:
        error_message = "Could not find ../../terraform/.secrets/.mapbox_token."
        error_message += "Have you got a Mapbox token and put it in this file?"
        error_message += "See the cleanair README for more details."
        raise FileNotFoundError(error_message)

    # evaluate the metrics
    metric_methods = metrics.get_metric_methods()
    precision_methods = metrics.get_precision_methods(pe1=metrics.probable_error)
    sensor_scores_df, temporal_scores_df = metrics.evaluate_model_data(
        instance.model_data,
        metric_methods,
        precision_methods=precision_methods,
        evaluate_training=evaluate_training,
    )
    # see the results in dashboard
    model_data_fit_app = apps.get_model_data_fit_app(
        instance.model_data,
        sensor_scores_df,
        temporal_scores_df,
        mapbox_access_token,
        evaluate_training=evaluate_training,
        all_metrics=list(metric_methods.keys()) + list(precision_methods.keys()),
    )
    model_data_fit_app.run_server(debug=True)


if __name__ == "__main__":
    main()
