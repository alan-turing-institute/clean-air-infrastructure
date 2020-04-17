"""API database queries"""
from sqlalchemy import func
from cleanair.loggers import initialise_logging
from cleanair.databases.tables import (
    ModelResult,
    MetaPoint,
    ScootReading,
    ScootDetector,
    ScootPercentChange,
)
from flask import jsonify
from .query_mixins import APIQueryMixin


initialise_logging(verbosity=0)


class ScootHourly(APIQueryMixin):
    @property
    def csv_headers(self):
        return [
            "detector_id",
            "lon",
            "lat",
            "measurement_start_utc",
            "measurement_end_utc",
            "day_of_week",
            "baseline_period",
            "baseline_n_vehicles_in_interval",
            "comparison_n_vehicles_in_interval",
            "percent_of_baseline",
        ]

    def query(self, session, start_time, end_time=None):
        """
        Get scoot data with lat and long positions
        """

        scoot_readings = (
            session.query(
                ScootReading.detector_id,
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
                ScootReading.measurement_start_utc,
                ScootReading.measurement_end_utc,
                ScootReading.n_vehicles_in_interval,
            )
            .join(ScootDetector, ScootReading.detector_id == ScootDetector.detector_n)
            .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
            .filter(ScootReading.measurement_start_utc >= start_time)
        )

        if end_time:

            scoot_readings = scoot_readings.filter(
                ScootReading.measurement_start_utc < end_time
            )

        scoot_readings = scoot_readings.order_by(
            ScootReading.detector_id, ScootReading.measurement_start_utc
        )

        return scoot_readings


class ScootDailyPerc(APIQueryMixin):

    @property
    def csv_headers(self):

        return [
            "detector_id",
            "measurement_start_utc",
            "measurement_end_utc",
            "day_of_week",
            "baseline_period",
            "baseline_start_date",
            "baseline_end_date",
            "baseline_n_vehicles_in_interval",
            "comparison_n_vehicles_in_interval",
            "percent_of_baseline",
            "no_traffic_in_baseline",
            "no_traffic_in_comparison ",
            "low_confidence ",
            "num_observations ",
            "removed_anomaly_from_baseline",
            "removed_anomaly_from_comparison",
        ]

    def query(self, session, baseline, start_time, end_time=None):

        percent_change = (
            session.query(
                ScootPercentChange,
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
            )
            .join(ScootDetector, ScootReading.detector_id == ScootDetector.detector_n)
            .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
            .filter(ScootPercentChange.measurement_start_utc >= start_time)
            .filter(ScootPercentChange.baseline_period == baseline)
        )

        if end_time:
            percent_change = percent_change.filter(
                ScootPercentChange.measurement_start_utc < end_time
            )

        return percent_change


class ScootDaily(APIQueryMixin):

    @property
    def csv_headers(self):

        return [
            "detector_id",
            "lon",
            "lat",
            "day",
            "avg_n_vehicles_in_interval",
            "sum_n_vehicles_in_interval",
        ]

    def query(self, session, start_time, end_time=None):
        """
        Get scoot data with lat and long positions aggregated by day
        """

        scoot_readings = (
            session.query(
                ScootReading.detector_id,
                func.date_trunc("day", ScootReading.measurement_start_utc).label("day"),
                func.avg(ScootReading.n_vehicles_in_interval).label(
                    "avg_n_vehicles_in_interval"
                ),
                func.sum(ScootReading.n_vehicles_in_interval).label(
                    "sum_n_vehicles_in_interval"
                ),
            )
            .group_by(
                ScootReading.detector_id,
                func.date_trunc("day", ScootReading.measurement_start_utc),
            )
            .filter(ScootReading.measurement_start_utc >= start_time)
        )

        if end_time:

            scoot_readings = scoot_readings.filter(
                ScootReading.measurement_start_utc < end_time
            )

        scoot_reading_cte = scoot_readings.cte("readings")

        summary_q = (
            session.query(
                scoot_reading_cte.c.detector_id,
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
                scoot_reading_cte.c.day,
                scoot_reading_cte.c.avg_n_vehicles_in_interval,
                scoot_reading_cte.c.sum_n_vehicles_in_interval,
            )
            .join(
                ScootDetector,
                scoot_reading_cte.c.detector_id == ScootDetector.detector_n,
            )
            .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
            .order_by(scoot_reading_cte.c.detector_id, scoot_reading_cte.c.day,)
        )

        return summary_q
