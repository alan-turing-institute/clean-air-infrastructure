"""Queries for the scoot dataset."""

from typing import Any, Iterable, List, Optional
from datetime import datetime
from sqlalchemy import func, or_, and_
import pandas as pd
from ...databases.tables import (
    MetaPoint,
    ScootDetector,
    ScootReading,
)
from ...decorators import db_query


class ScootQueryMixin:
    """Queries for the scoot dataset."""

    dbcnxn: Any

    @db_query
    def scoot_readings(
        self,
        start_time: str,
        end_time: Optional[str] = None,
        detectors: Optional[List] = None,
        with_location: bool = True,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        """
        Get scoot data with lat and long positions.

        Args:
            start_time: Start datetime.

        Keyword args:
            end_time: End datetime (exclusive).
            detectors: Subset of detectors to get readings for.
            with_location: If true return the lat, lon and geom columns for the location of the scoot detectors.
            offset: Start selecting detectors from this integer index.
            limit: Select at most this many detectors.

        """
        cols = [
            ScootReading.detector_id,
            ScootReading.measurement_start_utc,
            ScootReading.measurement_end_utc,
            ScootReading.n_vehicles_in_interval,
        ]
        if with_location:
            detector_query = self.scoot_detectors(
                detectors=detectors,
                offset=offset,
                limit=limit,
                output_type="subquery"
            )
            cols.extend(
                [
                    detector_query.c.lon,
                    detector_query.c.lat,
                    detector_query.c.location,
                ]
            )
        with self.dbcnxn.open_session() as session:
            scoot_readings = session.query(*cols).filter(
                ScootReading.measurement_start_utc >= start_time
            )
            if with_location:
                scoot_readings = scoot_readings.join(
                    detector_query, ScootReading.detector_id == detector_query.c.detector_id
                # ).join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
                )
            # get readings upto but not including end_time
            if end_time:
                scoot_readings = scoot_readings.filter(
                    ScootReading.measurement_start_utc < end_time
                )

            return scoot_readings

    @staticmethod
    def create_day_of_week_daterange(
        day_of_week: int, start_date: str, end_date: str
    ) -> Iterable:
        """Create a list of tuples (start date, end date) where each start_date is the same day of the week.

        Args:
            day_of_week: Day of the week. 0=Mon, 1=Tue, etc.
            start_date: ISO formatted date. All dates in returned list will be at least this date.
            end_date: ISO formatted date. All dates in the returned list will be at most this date.

        Returns
            List of date tuples. The first item in the tuple will be exactly one day before the last item in the tuple.
        """
        # get list of start times that match the weekday within the timerange
        starts = pd.date_range(start_date, end_date, closed="left").to_series()
        starts = (
            starts[(starts.dt.dayofweek == day_of_week) & (starts < end_date)]
            .dt.strftime("%Y-%m-%d")
            .to_list()
        )

        # get list of end times that match the weekday within the timerange
        ends = pd.date_range(start_date, end_date, closed="left").to_series()
        ends = (
            ends[(ends.dt.dayofweek == (day_of_week + 1) % 7) & (start_date < ends)]
            .dt.strftime("%Y-%m-%d")
            .to_list()
        )

        return zip(starts, ends)

    @db_query
    def get_scoot_by_dow(
        self,
        day_of_week: int,
        start_date: str,
        end_date: str = None,
        detectors: List = None,
    ):
        """
        Get scoot readings for days between start_date and end_date filtered by day_of_week.

        Args:
            day_of_week: Day of the week. 0=Mon, 1=Tue, etc.
            start_date: Start datetime.
            end_date: End datetime (exclusive).
            detectors: Subset of detectors to get readings for.
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        with self.dbcnxn.open_session() as session:
            scoot_readings = (
                session.query(
                    ScootReading.detector_id,
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                    ScootReading.measurement_start_utc,
                    ScootReading.measurement_end_utc,
                    ScootReading.n_vehicles_in_interval,
                )
                .join(
                    ScootDetector, ScootReading.detector_id == ScootDetector.detector_n
                )
                .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
            )
            # get a list of or statements
            or_statements = []
            for start, end in self.create_day_of_week_daterange(
                day_of_week, start_date, end_date
            ):
                # append AND statement
                or_statements.append(
                    and_(
                        ScootReading.measurement_start_utc >= start,
                        ScootReading.measurement_start_utc < end,
                    )
                )
            scoot_readings = scoot_readings.filter(or_(*or_statements))

            # get subset of detectors
            if detectors:
                scoot_readings = scoot_readings.filter(
                    ScootReading.detector_id.in_(detectors)
                )

            return scoot_readings

    @db_query
    def scoot_detectors(
        self, offset: Optional[int] = None, limit: Optional[int] = None, geom_label: str = "location", detectors: Optional[List] = None,
    ):
        """
        Get all scoot detectors from the interest point schema.

        Keyword args:
            offset: Start selecting detectors from this integer index.
            limit: Select at most this many detectors.
            geom_label: Rename the geometry column with this label.
            detectors: Only get detectors in this list.
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(
                ScootDetector.detector_n.label("detector_id"),
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
                MetaPoint.location.label(geom_label),
            ).join(MetaPoint, MetaPoint.id == ScootDetector.point_id)

            if offset and limit:
                readings = readings.order_by(ScootDetector.detector_n).slice(
                    offset, offset + limit
                )
            # get subset of detectors
            if detectors:
                readings = readings.filter(
                    ScootDetector.detector_n.in_(detectors)
                )

            return readings
