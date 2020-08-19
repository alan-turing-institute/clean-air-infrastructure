"""
The base class for metrics.
"""
import logging
from concurrent import futures
from typing import Collection

import pandas as pd
import gpflow

from cleanair.databases import DBWriter
from cleanair.databases.tables import TrafficMetricTable
from cleanair.loggers import get_logger

from .coverage import percent_coverage
from .nlpl import nlpl
from ..dataset import ScootDataset


class TrafficMetric(DBWriter):
    """
    The base class for metrics.
    """

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)
        self.metric_df = None

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @staticmethod
    def evaluate_model(model: gpflow.models.GPModel, dataset: ScootDataset) -> dict:
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
            coverage95=percent_coverage(
                model, dataset.features_tensor, dataset.target_tensor, quantile=0.95
            ),
            coverage75=percent_coverage(
                model, dataset.features_tensor, dataset.target_tensor, quantile=0.75
            ),
            coverage50=percent_coverage(
                model, dataset.features_tensor, dataset.target_tensor, quantile=0.50
            ),
            nlpl=nlpl(model, dataset.features_tensor, dataset.target_tensor),
        )

    def batch_evaluate_model(
        self,
        instance_ids: Collection[str],
        gp_models: Collection,
        scoot_datasets: Collection,
    ) -> pd.DataFrame:
        """
        Multi-process function for sampling from each model on x_test and evaluating against y_test.

        Args:
            instance_ids: List of instance ids.
            gp_models: List of gpflow models.
            scoot_datasets: List of traffic datasets.

        Returns:
            NLPL and coverage metrics with a column for ids.
        """
        assert len(instance_ids) == len(gp_models) == len(scoot_datasets)
        logging.info("Evaluating metrics for %s instances.", len(instance_ids))
        rows = []

        # start as many threads as number of CPUs
        with futures.ThreadPoolExecutor() as executor:
            tasks = {
                executor.submit(TrafficMetric.evaluate_model, model, dataset): dict(
                    instance_id=instance_id, data_id=dataset.data_id,
                )
                for instance_id, model, dataset in zip(
                    instance_ids, gp_models, scoot_datasets
                )
            }
            for future in futures.as_completed(tasks):
                logging.debug("Evaluated instance %s", tasks[future])
                rows.append(dict(**future.result(), **tasks[future]))

        logging.info("Finished evaluating metrics in batch mode.")
        self.metric_df = pd.DataFrame(rows)

    def update_remote_tables(self):
        """
        Save the metrics dataframe to the database.
        """
        if len(self.metric_df) == 0:
            self.logger.warning(
                "No metrics will be commited to the traffic metrics table - metric_df is empty."
            )
        # upload metrics to DB
        logging.info(
            "Inserting %s records into the traffic metrics table.", len(self.metric_df)
        )
        record_cols = [
            "instance_id",
            "data_id",
            "coverage50",
            "coverage75",
            "coverage95",
            "nlpl",
        ]
        upload_records = self.metric_df[record_cols].to_dict("records")
        self.commit_records(
            upload_records, on_conflict="overwrite", table=TrafficMetricTable
        )
