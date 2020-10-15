"""Queries for the scoot dataset."""

from __future__ import annotations
from typing import Any, Iterable, List, Optional, TYPE_CHECKING
from sqlalchemy import func, or_, and_
import pandas as pd
from ...databases.tables import (
    LondonBoundary,
    MetaPoint,
    ScootDetector,
    ScootReading,
)
from ...decorators import db_query

if TYPE_CHECKING:
    from datetime import datetime
    from ...types import Borough


class ScootQueryMixin:
    """Queries for the scoot dataset."""

    dbcnxn: Any

    @db_query()
    def scoot_detectors(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        geom_label: str = "location",
        detectors: Optional[List] = None,
        borough: Optional[Borough] = None,
    ):
        """
        Get all scoot detectors from the interest point schema.

        Keyword args:
            offset: Start selecting detectors from this integer index.
            limit: Select at most this many detectors.
            geom_label: Rename the geometry column with this label.
            detectors: Only get detectors in this list.
            borough: Only get detectors from this borough.
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(
                ScootDetector.detector_n.label("detector_id"),
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
                MetaPoint.location.label(geom_label),
                MetaPoint.id.label("point_id"),
            ).join(MetaPoint, MetaPoint.id == ScootDetector.point_id)

            # get subset of detectors
            if detectors is not None:
                readings = readings.filter(ScootDetector.detector_n.in_(detectors))

            # only get detectors in this borough
            if borough is not None:
                borough_sq = (
                    session.query(LondonBoundary)
                    .filter(LondonBoundary.name == borough.value)
                    .subquery()
                )
                readings = readings.filter(
                    func.ST_Intersects(MetaPoint.location, borough_sq.c.geom)
                )
            # limit / offset detectors
            if offset:
                readings = readings.offset(offset)
            if limit:
                readings = readings.limit(limit)

            return readings

    @db_query()
    def scoot_readings(
        self,
        start: datetime,
        upto: Optional[datetime] = None,
        with_location: bool = True,
        day_of_week: Optional[int] = None,
        detectors: Optional[List] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        borough: Optional[Borough] = None,
    ):
        """Get scoot data with lat and long positions.

        Args:
            start: Get readings from (including) this date(time). ISO format.

        Keyword args:
            upto: Get readings upto but not including this date(time).
            detectors: Subset of detectors to get readings for.
            with_location: If true return the lat, lon and geom columns for the location of the scoot detectors.
            day_of_week: Day of the week. 0=Mon, 1=Tue, etc.

        See also:
            `scoot_detectors` for docs on the other parameters.

        Raises:
            ValueError: If you pass `borough` without setting `with_location` to be True.
        """
        cols = [
            ScootReading.detector_id,
            ScootReading.measurement_start_utc,
            ScootReading.measurement_end_utc,
            ScootReading.n_vehicles_in_interval,
        ]
        if borough and not with_location:
            error_message = "If passing a borough, you must set `with_location` to True. You passed borough: %s"
            error_message = error_message.format(borough.value)
            return ValueError(error_message)

        not_implemented_error = (
            "You passed the {arg} argument. You should call scoot_detectors "
        )
        not_implemented_error += (
            "directly to use limit and offset before joining with scoot_readings."
        )
        not_implemented_error += " See this issue on GitHub "
        not_implemented_error += "https://github.com/alan-turing-institute/clean-air-infrastructure/issues/533"
        if limit is not None:
            raise NotImplementedError(not_implemented_error.format(arg="limit"))
        if offset is not None:
            raise NotImplementedError(not_implemented_error.format(arg="offset"))

        # get the location of detectors
        if with_location:
            detector_query = self.scoot_detectors(
                detectors=detectors,
                offset=offset,
                limit=limit,
                borough=borough,
                output_type="subquery",
            )
            cols.extend(
                [detector_query.c.lon, detector_query.c.lat, detector_query.c.location,]
            )
        with self.dbcnxn.open_session() as session:
            # query the selected columns and filter by start date(time)
            scoot_readings = session.query(*cols).filter(
                ScootReading.measurement_start_utc >= start
            )
            # add location if required
            if with_location:
                scoot_readings = scoot_readings.join(
                    detector_query,
                    ScootReading.detector_id == detector_query.c.detector_id,
                )
            # get readings upto but not including date(time)
            if upto:
                scoot_readings = scoot_readings.filter(
                    ScootReading.measurement_start_utc < upto
                )
            # filter by day of week
            if day_of_week:
                # get a list of or statements
                or_statements = []
                for start_date, upto_date in self.create_day_of_week_daterange(
                    day_of_week, start, upto
                ):
                    # append AND statement
                    or_statements.append(
                        and_(
                            ScootReading.measurement_start_utc >= start_date,
                            ScootReading.measurement_start_utc < upto_date,
                        )
                    )
                scoot_readings = scoot_readings.filter(or_(*or_statements))
            return scoot_readings

    @staticmethod
    def create_day_of_week_daterange(
        day_of_week: int, start_date: str, end_date: str
    ) -> Iterable:
        """Create a list of tuples (start date, end date) where each start_date is the same day of the week.

        Args:

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
