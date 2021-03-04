from datetime import datetime
from typing import Optional, List

from sqlalchemy import func

from ..databases import DBWriter
from ..databases.tables import MetaPoint, PointRoadMap
from ..decorators import db_query
from ..types.enum_types import Source


class PointRoadMapper(DBWriter):

    @db_query()
    def unprocessed_ids(self, sources=None, time=None):
        with self.dbcnxn.open_session() as session:
            processed_ids_query = session.query(PointRoadMap.point_id)
            if time:
                processed_ids_query = processed_ids_query.filter(PointRoadMap.map_datetime >= time)

            unprocessed_ids_query = session.query(MetaPoint.id) \
                .filter(MetaPoint.id.notin_(processed_ids_query))
            if sources:
                unprocessed_ids_query = unprocessed_ids_query \
                    .filter(MetaPoint.source in sources)

            return unprocessed_ids_query

    @db_query()
    def unprocessed_counts(self):

        ids = self.unprocessed_ids().all()

        with self.dbcnxn.open_session() as session:
            return session.query(MetaPoint.source, func.count(MetaPoint.id).label("unprocessed")).group_by(MetaPoint.source)

