"""
Methods for batching metric calculation.
"""

import logging
from collections.abc import Collection
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

def batch_metrics(
    ids: Collection,
    models: Collection,
    x_tests: Collection,
    y_tests: Collection,
) -> pd.DataFrame:
    """
    Multi-process function for sampling from each model on x_test and evaluating against y_test.

    Args:
        ids: List of instance ids.
        models: List of gpflow models.
        x_tests: List of numpy arrays of input data.
        y_tests: List of numpy arrays of actual count data.

    Returns:
        NLPL and coverage metrics with a column for ids.
    """
    assert len(ids) == len(models) == len(x_tests) == len(y_tests)
    logging.info("Evaluating metrics for %s instance in batch model.", len(ids))
    rows = []

    # start as many threads as number of CPUs
    with futures.ThreadPoolExecutor() as executor:
        tasks = {
            executor.submit(evaluate_metrics, model, x_test, y_test): instance_id
            for instance_id, model, x_test, y_test in zip(
                ids, models, x_tests, y_tests
            )
        }
        for future in futures.as_completed(tasks):
            logging.debug("Evaluated instance %s", tasks[future])
            rows.append(dict(**future.result(), instance_id=tasks[future]))

    logging.info("Finished evaluating metrics in batch mode.")
    return pd.DataFrame(rows)
