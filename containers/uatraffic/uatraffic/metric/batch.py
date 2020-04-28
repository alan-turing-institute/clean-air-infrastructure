"""
Methods for batching metric calculation.
"""

import logging
from concurrent import futures

import pandas as pd
import gpflow
import tensorflow as tf

from .coverage import percent_coverage
from .nlpl import nlpl

def evaluate_metrics(model: gpflow.models.GPModel, x_test: tf.Tensor, y_test: tf.Tensor) -> dict:
    """
    Run all metrics on a model given input data and actual observations.

    Args:
        model: Trained model to evaluate on test data.
        x_test: Test input data.
        y_test: Actual observations for input data.

    Returns:
        Dictionary where keys are the name of a metric and values are the evaluated metric.
    """
    return dict(
        coverage95=percent_coverage(model, x_test, y_test, quantile=0.95),
        coverage75=percent_coverage(model, x_test, y_test, quantile=0.75),
        coverage50=percent_coverage(model, x_test, y_test, quantile=0.50),
        nlpl=nlpl(model, x_test, y_test),
    )

def batch_metrics(ids: list, models: list, x_tests: list, y_tests: list) -> pd.DataFrame:
    """
    Multi-process function for sampling from each model on x_test and evaluating against y_test.

    Args:
        ids: List of instance ids.
        models: List of gpflow models.
        x_tests: List of numpy arrays of input data.
        y_tetss: List of numpy arrays of actual count data.

    Returns:
        NLPL and coverage metrics with a column for ids.
    """
    logging.info("Evaluating metrics for %s instance in batch model.")
    rows = []
    # start as many processes as number of CPUs
    with futures.ProcessPoolExecutor() as executor:
        for instance_id, results in zip(ids, executor.map(
            evaluate_metrics, models, x_tests, y_tests
        )):
            rows.append(dict(results, instance_id=instance_id))
    return pd.DataFrame(rows)
