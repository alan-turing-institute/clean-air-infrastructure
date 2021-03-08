from typing import List

from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import literal
from sqlalchemy.types import Float

from ..databases import DBWriter
from ..databases.tables import MetaPoint, PointRoadMap, OSHighway
from ..decorators import db_query


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
                    .filter(MetaPoint.source.in_(sources))

            return unprocessed_ids_query

    @db_query()
    def unprocessed_counts(self, sources=None):

        ids = self.unprocessed_ids(sources=sources).all()

        with self.dbcnxn.open_session() as session:
            return session.query(MetaPoint.source, func.count(MetaPoint.id).label("unprocessed")).group_by(MetaPoint.source)

    @db_query()
    def buffers(self, point_ids: List[str], radius: float):
        with self.dbcnxn.open_session() as session:
            return session.query(
                MetaPoint.id.label("id"),
                func.Geometry(func.ST_Buffer(func.Geography(MetaPoint.location), radius)).label("geom")
            ).filter(MetaPoint.id.in_(point_ids))

    @db_query()
    def map_points(self, point_ids: List[str]):
        with self.dbcnxn.open_session() as session:
            for radius in [10, 100, 200, 500, 1000]:
                buffers = self.buffers(point_ids=point_ids, radius=radius).cte("buffer")

                maps = (
                    session.query(
                        buffers.c.id.label("point_id"),
                        OSHighway.toid.label("road_segment_id"),
                        literal(radius, Float).label("buffer_radius"),
                        func.now().label("map_datetime")
                    )
                        .filter(func.ST_Intersects(buffers.c.geom, OSHighway.geom))
                        .subquery()
                )

                self.commit_records(
                    maps,
                    on_conflict="overwrite",
                    table=PointRoadMap
                )
