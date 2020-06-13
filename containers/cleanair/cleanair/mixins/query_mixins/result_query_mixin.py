"""Mixin for querying from the result table."""

from typing import Any
from sqlalchemy import func
from ...databases.mixins import ResultTableMixin
from ...databases.tables import MetaPoint
from ...decorators import db_query


class ResultQueryMixin:
    """Mixin for querying results."""

    result_table: ResultTableMixin
    dbcnxn: Any     # TODO what is this type?

    @db_query
    def from_instance_id(self, instance_id: str):
        """Get the predictions of a model for a given instance id.

        Args:
            instance_id: The id of the trained model instance.
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
            return readings
