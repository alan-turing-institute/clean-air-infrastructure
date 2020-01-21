"""
Mixin for useful database queries
"""

from sqlalchemy import func
from sqlalchemy import null, literal, and_
from ..decorators import db_query
from ..databases.tables import (
    LondonBoundary,
    IntersectionValue,
    IntersectionValueDynamic,
    MetaPoint,
    AQESite,
    LAQNSite,
    LAQNReading,
    AQEReading,
)
from ..loggers import get_logger


class DBQueryMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(
                func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom))
            )
        return hull

    @db_query
    def get_available_static_features(self):
        """Return available static features from the CleanAir database
        """

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(IntersectionValue.feature_name).distinct(
                IntersectionValue.feature_name
            )

            return feature_types_q

    @db_query
    def get_available_dynamic_features(self, start_date, end_date):
        """Return a list of the available dynamic features in the database.
            Only returns features that are available between start_date and end_date
        """

        with self.dbcnxn.open_session() as session:

            available_dynamic_sq = (
                session.query(
                    IntersectionValueDynamic.feature_name,
                    func.min(IntersectionValueDynamic.measurement_start_utc).label(
                        "min_date"
                    ),
                    func.max(IntersectionValueDynamic.measurement_start_utc).label(
                        "max_date"
                    ),
                )
                .group_by(IntersectionValueDynamic.feature_name)
                .subquery()
            )

            available_dynamic_q = session.query(available_dynamic_sq).filter(
                and_(
                    available_dynamic_sq.c["min_date"] <= start_date,
                    available_dynamic_sq.c["max_date"] >= end_date,
                )
            )

            return available_dynamic_q

    @db_query
    def get_available_sources(self):
        """Return the available interest point sources in a database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(MetaPoint.source).distinct(MetaPoint.source)

            return feature_types_q

    @db_query
    def get_available_interest_points(self, sources):
        """Return the available interest points for a list of sources, excluding any LAQN or AQE sites that are closed.
        Only returns points withing the London boundary
        Satellite returns features outside of london boundary, while laqn and aqe do not.
        args:
            sources: A list of sources to include
        """

        bounded_geom = self.query_london_boundary()
        base_query_columns = [
            MetaPoint.id.label("point_id"),
            MetaPoint.source.label("source"),
            MetaPoint.location.label("location"),
            MetaPoint.location.ST_Within(bounded_geom).label("in_london"),
            func.ST_X(MetaPoint.location).label("lon"),
            func.ST_Y(MetaPoint.location).label("lat"),
        ]

        with self.dbcnxn.open_session() as session:

            remaining_sources_q = session.query(
                *base_query_columns,
                null().label("date_opened"),
                null().label("date_closed"),
            ).filter(
                MetaPoint.source.in_(
                    [
                        source
                        for source in sources
                        if source not in ["laqn", "aqe", "satellite"]
                    ]
                ),
                MetaPoint.location.ST_Within(bounded_geom),
            )

            # Satellite is not filtered by london boundary
            sat_sources_q = session.query(
                *base_query_columns,
                null().label("date_opened"),
                null().label("date_closed"),
            ).filter(MetaPoint.source.in_(["satellite"]))

            aqe_sources_q = (
                session.query(
                    *base_query_columns, AQESite.date_opened, AQESite.date_closed
                )
                .join(AQESite, isouter=True)
                .filter(
                    MetaPoint.source.in_(["aqe"]),
                    MetaPoint.location.ST_Within(bounded_geom),
                )
            )

            laqn_sources_q = (
                session.query(
                    *base_query_columns, LAQNSite.date_opened, LAQNSite.date_closed
                )
                .join(LAQNSite, isouter=True)
                .filter(
                    MetaPoint.source.in_(["laqn"]),
                    MetaPoint.location.ST_Within(bounded_geom),
                )
            )

            if ("satellite" in sources) and (len(sources) != 1):
                raise ValueError(
                    """Satellite can only be requested on a source on its own.
                    Ensure 'sources' contains no other options"""
                )
            if sources[0] == "satellite":
                all_sources_sq = remaining_sources_q.union(sat_sources_q).subquery()
            else:
                all_sources_sq = remaining_sources_q.union(
                    aqe_sources_q, laqn_sources_q
                ).subquery()

            # Remove any sources where there is a closing date
            all_sources_q = session.query(all_sources_sq).filter(
                all_sources_sq.c.date_closed.is_(None)
            )

        return all_sources_q

    @db_query
    def get_laqn_readings(self, start_date, end_date):
        """Get laqn readings from the database"""
        with self.dbcnxn.open_session() as session:
            laqn_reading_q = session.query(
                LAQNReading.measurement_start_utc,
                LAQNReading.species_code,
                LAQNReading.value,
                LAQNSite.point_id,
                literal("laqn").label("source"),
            ).join(LAQNSite)
            laqn_reading_q = laqn_reading_q.filter(
                LAQNReading.measurement_start_utc >= start_date,
                LAQNReading.measurement_start_utc < end_date,
            )
            return laqn_reading_q

    @db_query
    def get_aqe_readings(self, start_date, end_date):
        """Get AQE readings from the database"""
        with self.dbcnxn.open_session() as session:
            aqe_reading_q = session.query(
                AQEReading.measurement_start_utc,
                AQEReading.species_code,
                AQEReading.value,
                AQESite.point_id,
                literal("aqe").label("source"),
            ).join(AQESite)
            aqe_reading_q = aqe_reading_q.filter(
                AQEReading.measurement_start_utc >= start_date,
                AQEReading.measurement_start_utc < end_date,
            )
            return aqe_reading_q
