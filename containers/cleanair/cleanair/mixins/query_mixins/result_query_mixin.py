"""Mixin for querying from the result table."""

from abc import abstractmethod
from typing import Any, Optional
from sqlalchemy import func

from ...databases.mixins import ResultTableMixin
from ...databases.tables import MetaPoint
from ...decorators import db_query


class ResultQueryMixin:
    """Mixin for querying results."""

    dbcnxn: Any  # TODO what is this type?

    @property
    @abstractmethod
    def result_table(self) -> ResultTableMixin:
        """The sqlalchemy table to query. The table must extend ResultTableMixin."""

    @db_query
    def query_results(self, instance_id: str, data_id: Optional[str]):
        """Get the predictions from a model given an instance and data id.

        Args:
            instance_id: The id of the trained model instance.
            data_id: The id of the dataset the model predicted on.
        """
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(
                    self.result_table,
                    MetaPoint.source,
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                )
                .filter(self.result_table.instance_id == instance_id)
                .join(MetaPoint, self.result_table.point_id == MetaPoint.id)
            )
            # filter by data id too
            if data_id:
                readings = readings.filter(self.result_table.data_id == data_id)
            return readings
