"""Mixin class for predictions from a model."""

from abc import abstractmethod
from logging import Logger
from typing import Optional
import pandas as pd
from sqlalchemy import inspect
from ...databases.mixins import ResultTableMixin
from ...loggers import get_logger


class ResultMixin:
    """The predictions from an air quality model.

    Attributes:
        instance_id: Id of the trained model.
        data_id: Id of the test dataset.
        result_df: Dataframe of predictions from the model.
    """

    def __init__(
        self,
        instance_id: str,
        data_id: str,
        result_df: pd.DataFrame,
        secretfile: Optional[str] = None,
        logger: Logger = get_logger("result"),
        **kwargs,
    ):
        super().__init__(secretfile=secretfile, **kwargs)
        self.instance_id = instance_id
        self.data_id = data_id
        self.logger = logger
        self.result_df = result_df
        if "instance_id" not in self.result_df:
            self.result_df["instance_id"] = self.instance_id
        if "data_id" not in self.result_df:
            self.result_df["data_id"] = self.data_id

    @property
    @abstractmethod
    def result_table(self) -> ResultTableMixin:
        """The sqlalchemy table to query. The table must extend ResultTableMixin."""

    def update_remote_tables(self):
        """Write air quality results to the database."""
        # get column names of result table
        inst = inspect(self.result_table)
        record_cols = [c_attr.key for c_attr in inst.mapper.column_attrs]

        # filter dataframe by selecting only columns that will be commited to db
        # then convert to records
        records = self.result_df.loc[
            :, self.result_df.columns.isin(record_cols)
        ].to_dict("records")

        # commit the records to the air quality results table
        self.logger.info(
            "Writing %s records to the air quality result table", len(records)
        )
        self.commit_records(records, table=self.result_table, on_conflict="ignore")
