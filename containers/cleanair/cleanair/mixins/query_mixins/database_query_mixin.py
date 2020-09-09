"""
Mixin for useful database queries
"""
from typing import List
from datetime import datetime
from sqlalchemy import func
from ...decorators import db_query
from ...databases.materialised_views import LondonBoundaryView
from ...databases.tables import (
    AQEReading,
    AQESite,
    LAQNReading,
    LAQNSite,
    SatelliteForecast,
    SatelliteGrid,
)
from ...loggers import get_logger
from ...timestamps import as_datetime
from ...types import Species


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
        """Query LondonBoundary to obtain the bounding geometry for London.
        Only get the first row as should only be one entry"""
        with self.dbcnxn.open_session() as session:

            return session.query(LondonBoundaryView.geom).limit(1)

    @db_query
    def get_laqn_readings(
        self, start_date: datetime, end_date: datetime, species: List[Species]
    ):
        """Get LAQN readings from database"""

        species = [spec.value for spec in species]

        with self.dbcnxn.open_session() as session:
            laqn_reading_q = (
                session.query(
                    LAQNSite.point_id,
                    LAQNReading.measurement_start_utc,
                    LAQNReading.species_code,
                    LAQNReading.value,
                )
                .join(LAQNSite)
                .filter(
                    LAQNReading.measurement_start_utc >= start_date.isoformat(),
                    LAQNReading.measurement_start_utc < end_date.isoformat(),
                    LAQNReading.species_code.in_(species),
                    LAQNReading.value.isnot(None),
                )
            )
            return laqn_reading_q

    @db_query
    def get_aqe_readings(
        self, start_date: datetime, end_date: datetime, species: List[Species]
    ):
        """Get AQE readings from database"""

        species = [spec.value for spec in species]

        with self.dbcnxn.open_session() as session:
            aqe_reading_q = (
                session.query(
                    AQESite.point_id,
                    AQEReading.measurement_start_utc,
                    AQEReading.species_code,
                    AQEReading.value,
                )
                .join(AQESite)
                .filter(
                    AQEReading.measurement_start_utc >= start_date.isoformat(),
                    AQEReading.measurement_start_utc < end_date.isoformat(),
                    AQEReading.species_code.in_(species),
                    AQEReading.value.isnot(None),
                )
            )
            return aqe_reading_q

    @db_query
    def get_satellite_readings(
        self, start_date: datetime, end_date: datetime, species: List[Species]
    ):
        """Get Satellite data
           As we get 72 hours of Satellite forecast on each day,
           here we only get Satellite data where the reference date
           is the same as the forecast time.
           i.e. Get data between start_datetime and end_datetime which
           consists of the first 24 hours of forecasts on each of those days
        """

        all_species = [spc.value for spc in species]

        with self.dbcnxn.open_session() as session:

            # The sort by is very important for creating numpy arrays
            sat_q = (
                session.query(
                    SatelliteForecast.measurement_start_utc,
                    SatelliteForecast.box_id,
                    SatelliteForecast.species_code,
                    SatelliteForecast.value,
                    SatelliteGrid.point_id,
                )
                .filter(
                    SatelliteForecast.measurement_start_utc >= start_date.isoformat(),
                    SatelliteForecast.measurement_start_utc < end_date.isoformat(),
                    func.date(SatelliteForecast.measurement_start_utc)
                    == func.date(SatelliteForecast.reference_start_utc),
                    SatelliteForecast.species_code.in_(all_species),
                )
                .join(SatelliteGrid, SatelliteForecast.box_id == SatelliteGrid.box_id)
                .order_by(
                    SatelliteForecast.box_id,
                    SatelliteForecast.measurement_start_utc,
                    SatelliteGrid.point_id,
                )
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
