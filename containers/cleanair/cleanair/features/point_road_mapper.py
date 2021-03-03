from Typing import Optional, List, Datetime

from ..databases import DBWriter
from ..databases.tables import MetaPoint, RoadPointMap
from ..types.enum_types import Source


class PointRoadMapper(DBWriter):

    @db_query()
    def unprocessed_ids(self, sources: List[Source], datetime: Optional[Datetime]):
        with self.dbcnxn.open_session() as session:
            processed_ids_query = session.query(RoadPointMap.point_id)
            if datetime:
                processed_ids_query = processed_ids_query.filter(RoadPointMap.map_datetime >= datetime)

            return (session.query(MetaPoint.id)
                    .filter(MetaPoint.id.notin_(processed_ids_query))
                    .filter(MetaPoint.source in sources)
                    )
