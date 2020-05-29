"""API database queries"""
from sqlalchemy import func, text
from cleanair.loggers import initialise_logging
from cleanair.decorators import db_query
from cleanair.databases.tables import (
    MetaPoint,
    ScootReading,
    ScootDetector,
    ScootPercentChange,
)
from odysseus.dates import (
    LOCKDOWN_BASELINE_END,
    NORMAL_BASELINE_END,
)
from .query_mixins import APIQueryMixin

initialise_logging(verbosity=0)

ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class ScootPercAvailability(APIQueryMixin):
    @db_query
    def query(
        self, session, baseline, start_time=None, end_time=None, only_missing=False
    ):
        """Check what data is available between start_time and end_time"""

        in_data = session.query(
            func.count(ScootPercentChange.detector_id).label("sensors_with_readings"),
            ScootPercentChange.measurement_start_utc,
        ).filter(ScootPercentChange.baseline_period == baseline)

        if start_time:
            in_data = in_data.filter(
                ScootPercentChange.measurement_start_utc >= start_time
            )
        if end_time:
            in_data = in_data.filter(
                ScootPercentChange.measurement_start_utc < end_time
            )

        if not (start_time and end_time) and baseline == "normal":
            start_time = NORMAL_BASELINE_END

        elif not (start_time and end_time) and baseline == "lockdown":
            start_time = LOCKDOWN_BASELINE_END

        in_data_cte = in_data.group_by(ScootPercentChange.measurement_start_utc).cte(
            "in_data"
        )

        if end_time:
            expected_date_times = session.query(
                func.generate_series(start_time, end_time, ONE_DAY_INTERVAL).label(
                    "measurement_start_utc"
                )
            ).subquery()
        else:
            expected_date_times = session.query(
                func.generate_series(
                    start_time,
                    func.date_trunc("day", func.now()) - ONE_DAY_INTERVAL,
                    ONE_DAY_INTERVAL,
                ).label("measurement_start_utc")
            ).subquery()

        available_data_q = (
            session.query(
                expected_date_times.c.measurement_start_utc,
                in_data_cte.c.sensors_with_readings,
                in_data_cte.c.sensors_with_readings.is_(None).label("no_data"),
                (in_data_cte.c.sensors_with_readings < 9000).label("less_than_9000"),
            )
            .select_entity_from(expected_date_times)
            .join(
                in_data_cte,
                in_data_cte.c.measurement_start_utc
                == expected_date_times.c.measurement_start_utc,
                isouter=True,
            )
        )

        if only_missing:
            return available_data_q.filter(
                in_data_cte.c.sensors_with_readings.is_(None)
            )
        else:
            return available_data_q


class ScootHourlyAvailability(APIQueryMixin):
    @db_query
    def query(self, session, start_time, end_time=None, only_missing=False):
        """Check what data is available between start_time and end_time"""

        in_data = session.query(
            func.count(ScootReading.detector_id).label("sensors_with_readings"),
            ScootReading.measurement_start_utc,
        ).filter(ScootReading.measurement_start_utc >= start_time)
        if end_time:
            in_data = in_data.filter(ScootReading.measurement_start_utc < end_time)

        in_data_cte = in_data.group_by(ScootReading.measurement_start_utc).cte(
            "in_data"
        )

        if end_time:
            expected_date_times = session.query(
                func.generate_series(start_time, end_time, ONE_HOUR_INTERVAL).label(
                    "measurement_start_utc"
                )
            ).subquery()
        else:
            expected_date_times = session.query(
                func.generate_series(start_time, func.now(), ONE_HOUR_INTERVAL).label(
                    "measurement_start_utc"
                )
            ).subquery()

        available_data_q = (
            session.query(
                expected_date_times.c.measurement_start_utc,
                in_data_cte.c.sensors_with_readings,
                in_data_cte.c.sensors_with_readings.is_(None).label("no_data"),
                (in_data_cte.c.sensors_with_readings < 9000).label("less_than_9000"),
            )
            .select_entity_from(expected_date_times)
            .join(
                in_data_cte,
                in_data_cte.c.measurement_start_utc
                == expected_date_times.c.measurement_start_utc,
                isouter=True,
            )
        )

        if only_missing:
            return available_data_q.filter(
                in_data_cte.c.sensors_with_readings.is_(None)
            )
        else:
            return available_data_q


class ScootHourly(APIQueryMixin):
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
    @db_query
    def query(
        self,
        session,
        start_time,
        end_time,
        baseline,
        exclude_baseline_no_traffic,
        exclude_comparison_no_traffic,
        exclude_low_confidence,
        return_meta,
    ):

        meta_cols = [
            ScootPercentChange.measurement_end_utc,
            ScootPercentChange.day_of_week,
            ScootPercentChange.comparison_n_vehicles_in_interval,
            ScootPercentChange.baseline_period,
            ScootPercentChange.baseline_start_date,
            ScootPercentChange.baseline_end_date,
            ScootPercentChange.no_traffic_in_baseline,
            ScootPercentChange.no_traffic_in_comparison,
            ScootPercentChange.low_confidence,
            ScootPercentChange.num_observations,
            ScootPercentChange.removed_anomaly_from_baseline,
            ScootPercentChange.removed_anomaly_from_comparison,
        ]

        data_cols = [
            ScootPercentChange.detector_id,
            ScootPercentChange.measurement_start_utc,
            ScootPercentChange.baseline_n_vehicles_in_interval,
            ScootPercentChange.percent_of_baseline,
            func.ST_X(MetaPoint.location).label("lon"),
            func.ST_Y(MetaPoint.location).label("lat"),
        ]

        if return_meta:
            all_cols = data_cols + meta_cols
        else:
            all_cols = data_cols

        percent_change = (
            session.query(*all_cols)
            .join(
                ScootDetector,
                ScootPercentChange.detector_id == ScootDetector.detector_n,
            )
            .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
            .filter(ScootPercentChange.measurement_start_utc >= start_time)
            .filter(ScootPercentChange.baseline_period == baseline)
        )

        if end_time:
            percent_change = percent_change.filter(
                ScootPercentChange.measurement_start_utc < end_time
            )

        if exclude_baseline_no_traffic:
            percent_change = percent_change.filter(
                ScootPercentChange.no_traffic_in_baseline != True
            )

        if exclude_comparison_no_traffic:
            percent_change = percent_change.filter(
                ScootPercentChange.no_traffic_in_comparison != True
            )

        if exclude_low_confidence:
            percent_change = percent_change.filter(
                ScootPercentChange.low_confidence != True
            )

        percent_change = percent_change.order_by(
            ScootPercentChange.measurement_start_utc
        )
        return percent_change


class ScootDaily(APIQueryMixin):
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
