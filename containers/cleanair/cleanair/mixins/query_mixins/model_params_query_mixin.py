"""Mixin for query the model params table."""

from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING
from abc import abstractmethod
from ...databases.mixins import ModelTableMixin
from ...decorators import db_query
from ...types import ModelName

if TYPE_CHECKING:
    from ...databases import Connector


class ModelParamsQueryMixin:
    """Class for querying model parameters."""

    dbcnxn: Connector

    @property
    @abstractmethod
    def model_table(self) -> ModelTableMixin:
        """The sqlalchemy table to query. The table must extend ResultTableMixin."""

    @db_query
    def query_model_params(
        self,
        model_name: ModelName,
        kernel: Optional[str] = None,
        maxiter: Optional[int] = None,
        param_id: Optional[str] = None,
    ) -> Any:
        """Query the model params table, filtering by arguments.

        Args:
            model_name: Name of the model trained.

        Keyword args:
            kernel: Name of a kernel to filter by.
            maxiter: Number of iterations to train model for.
            param_id: The ID of the model parameters. Specifiying this
                argument will likely mean only one row is returned.

        Returns:
            Database query with columns for param id, model name and model params.
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(self.model_table).filter(
                self.model_table.model_name == model_name
            )
            # maxiter is a first-level for most models except mrdgp
            if (maxiter or kernel) and model_name == ModelName.mrdgp:
                raise NotImplementedError(
                    "There are multiple maxiter and kernel parameters for the MR Deep GP."
                )
            if kernel:
                readings = readings.filter(
                    self.model_table.model_params["kernel"]["name"].astext == kernel
                )
            if maxiter:
                readings = readings.filter(
                    self.model_table.model_params["maxiter"] == maxiter
                )
            if param_id:
                readings = readings.filter(self.model_table.param_id == param_id)
            return readings
