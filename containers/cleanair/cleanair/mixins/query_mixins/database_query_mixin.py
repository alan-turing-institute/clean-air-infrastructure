"""
Mixin for useful database queries
"""

from sqlalchemy import and_, func, literal, null
from ...decorators import db_query
from ...databases.materialised_views import LondonBoundaryView
from ...databases.tables import (
    AQEReading,
    AQESite,
    StaticFeature,
    DynamicFeature,
    LAQNReading,
    LAQNSite,
    LondonBoundary,
    MetaPoint,
    SatelliteForecast,
)
from ...loggers import get_logger
from ...timestamps import as_datetime


class DBQueryMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London. Only get the first row as should only be one entry"""
        with self.dbcnxn.open_session() as session:

            return session.query(LondonBoundaryView.geom).limit(1)

    @db_query
    def get_available_static_features(self):
        """Return available static features from the CleanAir database
        """

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(StaticFeature.feature_name).distinct(
                StaticFeature.feature_name
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
                    DynamicFeature.feature_name,
                    func.min(DynamicFeature.measurement_start_utc).label("min_date"),
                    func.max(DynamicFeature.measurement_start_utc).label("max_date"),
                )
                .group_by(DynamicFeature.feature_name)
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
    def get_available_interest_points(self, sources, point_ids=None):
        """Return the available interest points for a list of sources, excluding any LAQN or AQE sites that are closed.
        Only returns points withing the London boundary
        Satellite returns features outside of london boundary, while laqn and aqe do not.
        args:
            sources: A list of sources to include
            point_ids: A list of point_ids to include. Default of None returns all points
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
                    *base_query_columns,
                    func.min(AQESite.date_opened),
                    func.min(AQESite.date_closed),
                )
                .join(AQESite, isouter=True)
                .group_by(*base_query_columns)
                .filter(
                    MetaPoint.source.in_(["aqe"]),
                    MetaPoint.location.ST_Within(bounded_geom),
                )
            )

            laqn_sources_q = (
                session.query(
                    *base_query_columns,
                    func.min(LAQNSite.date_opened),
                    func.min(LAQNSite.date_closed),
                )
                .join(LAQNSite, isouter=True)
                .group_by(*base_query_columns)
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

            # Remove any sources where there is a closing date and filter by point_ids
            all_sources_q = session.query(all_sources_sq).filter(
                all_sources_sq.c.date_closed.is_(None)
            )

            if point_ids:
                all_sources_q = all_sources_q.filter(
                    all_sources_sq.c.point_id.in_(point_ids)
                )

        return all_sources_q

    @db_query
    def get_laqn_readings(self, start_date, end_date):
        """Get LAQN readings from database"""
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
        """Get AQE readings from database"""
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

    @db_query
    def get_satellite_readings_training(self, start_date, end_date, species):
        """Get Satellite data for the training period
           As we get 72 hours of Satellite forecast on each day,
           here we only get Satellite data where the reference date
           is the same as the forecast time.
           i.e. Get data between start_datetime and end_datetime which
           consists of the first 24 hours of forecasts on each of those days
        """

        with self.dbcnxn.open_session() as session:

            sat_q = session.query(SatelliteForecast).filter(
                SatelliteForecast.measurement_start_utc >= start_date,
                SatelliteForecast.measurement_start_utc < end_date,
                func.date(SatelliteForecast.measurement_start_utc)
                == func.date(SatelliteForecast.reference_start_utc),
                SatelliteForecast.species_code.in_(species),
            )

            return sat_q

    @db_query
    def get_satellite_readings_pred(self, start_date, end_date, species):
        """Get Satellite data for the prediction period
           Gets up to 72 hours of predicted data from the satellite readings
           from the same reference_start_utc date as start_date
        """

        if (
            int(
                (as_datetime(end_date) - as_datetime(start_date)).total_seconds()
                // 60
                // 60
            )
            > 72
        ):
            raise ValueError(
                "You may only request forecast data up to 72 hours from start_date"
            )

        with self.dbcnxn.open_session() as session:
            return session.query(SatelliteForecast).filter(
                SatelliteForecast.measurement_start_utc >= start_date,
                SatelliteForecast.measurement_start_utc < end_date,
                func.date(SatelliteForecast.reference_start_utc)
                == as_datetime(start_date).date().isoformat(),
                SatelliteForecast.species_code.in_(species),
            )
