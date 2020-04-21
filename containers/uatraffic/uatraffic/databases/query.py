"""
Class for querying traffic and scoot data.
"""

import json
from datetime import datetime
import pandas as pd
from sqlalchemy import func, or_, and_, not_, Integer

from cleanair.databases import DBWriter, DBReader
from cleanair.databases.tables import (
    OSHighway,
    MetaPoint,
    ScootReading,
    ScootDetector,
    ScootPercentChange,
)
from cleanair.decorators import db_query
from cleanair.loggers import get_logger

from .tables import TrafficInstanceTable, TrafficModelTable, TrafficDataTable, TrafficMetric


class TrafficQuery(DBWriter):
    """
    Queries to run on the SCOOT DB.
    """

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def get_scoot_with_location(self, start_time, end_time=None, detectors=None):
        """
        Get scoot data with lat and long positions.

        Parameters
        ___

        start_time : str
            Start datetime.

        end_time : str, optional
            End datetime (exclusive).

        detectors : list, optional
            Subset of detectors to get readings for.
        """

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
                .filter(ScootReading.measurement_start_utc >= start_time)
            )
            # get readings upto but not including end_time
            if end_time:

                scoot_readings = scoot_readings.filter(
                    ScootReading.measurement_start_utc < end_time
                )
            # get subset of detectors
            if detectors:
                scoot_readings = scoot_readings.filter(
                    ScootReading.detector_id.in_(detectors)
                )

            return scoot_readings

    @db_query
    def get_scoot_filter_by_dow(self, day_of_week, start_time, end_time=None, detectors=None):
        """
        Get scoot readings for days between start_time and end_time filtered by day_of_week.

        Parameters
        ___

        day_of_week : int
            Day of the week. 0=Mon, 1=Tue, etc.

        start_time : str
            Start datetime.

        end_time : str, optional
            End datetime (exclusive).

        detectors : list, optional
            Subset of detectors to get readings for.
        """
        if not end_time:
            end_time = datetime.now().strftime("%Y-%m-%d")

        # get list of start times that match the weekday within the timerange
        starts = pd.date_range(start_time, end_time).to_series()
        starts = starts[(starts.dt.dayofweek == day_of_week) & (starts < end_time)].dt.strftime("%Y-%m-%d").to_list()

        # get list of end times that match the weekday within the timerange
        ends = pd.date_range(start_time, end_time).to_series()
        ends = ends[(ends.dt.dayofweek == (day_of_week + 1) % 7) & (ends > start_time)].dt.strftime("%Y-%m-%d").to_list()

        # check lists are the same length
        assert len(starts) == len(ends)

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
            for s, e in zip(starts, ends):
                # append AND statement
                or_statements.append(and_(
                    ScootReading.measurement_start_utc >= s,
                    ScootReading.measurement_start_utc < e
                ))
            scoot_readings = scoot_readings.filter(or_(*or_statements))

            # get subset of detectors
            if detectors:
                scoot_readings = scoot_readings.filter(
                    ScootReading.detector_id.in_(detectors)
                )

            return scoot_readings

    @db_query
    def get_percent_of_baseline(self, baseline_period, comparison_start, comparison_end=None, detectors=None):
        """
        Get the values for the percent_of_baseline metric for a day and baseline.
        """
        with self.dbcnxn.open_session() as session:
            baseline_readings = (
                session.query(ScootPercentChange)
                .filter(ScootPercentChange.baseline_period == baseline_period)
                .filter(ScootPercentChange.measurement_start_utc >= comparison_start)
            )
            if comparison_end:
                baseline_readings = baseline_readings.filter(
                    ScootPercentChange.measurement_start_utc < comparison_end
                )
            # get subset of detectors
            if detectors:
                baseline_readings = baseline_readings.filter(
                    ScootReading.detector_id.in_(detectors)
                )
            return baseline_readings

    @db_query
    def get_scoot_detectors(self, start=None, end=None):
        """
        Get all scoot detectors from the interest point schema.
        """
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(
                    ScootDetector.detector_n.label("detector_id"),
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                )
                .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
            )

            if isinstance(start, int) and isinstance(end, int):
                readings = readings.order_by(ScootDetector.detector_n).slice(start, end)

            return readings

class TrafficInstanceQuery(DBReader):
    """
    Class for querying traffic model instances.
    """

    @db_query
    def get_instances(
        self,
        tag: str = None,
        instance_ids: list = None,
        data_ids: list = None,
        param_ids: list = None,
        models: list = None
    ):
        """
        Get traffic instances and optionally filter by parameters.
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(TrafficInstanceTable)
            # filter by tag
            if tag:
                readings = readings.filter(TrafficInstanceTable.tag == tag)
            # filter by instance ids
            if instance_ids:
                readings = readings.filter(TrafficInstanceTable.instance_id.in_(instance_ids))
            # filter by data ids
            if data_ids:
                readings = readings.filter(
                    TrafficInstanceTable.data_id.in_(data_ids)
                )
            # filter by param ids and model name
            if param_ids:
                readings = readings.filter(
                    TrafficInstanceTable.param_id.in_(param_ids)
                )
            # filter by model names
            if models:
                readings = readings.filter(
                    TrafficInstanceTable.model_name.in_(models)
                )
            return readings

    @db_query
    def get_instances_with_params(
        self,
        tag: str = None,
        instance_ids: list = None,
        data_ids: list = None,
        param_ids: list = None,
        models: list = None
    ):
        """
        Get all traffic instances and join the json parameters.
        """
        instance_subquery = self.get_instances(tag=tag, instance_ids=instance_ids, data_ids=data_ids, param_ids=param_ids, models=models, output_type="subquery")
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(
                    instance_subquery,
                    TrafficModelTable.model_param,
                    TrafficDataTable.data_config,
                )
                .join(
                    TrafficModelTable,
                    and_(
                        TrafficModelTable.model_name == TrafficInstanceTable.model_name,
                        TrafficModelTable.param_id == TrafficInstanceTable.param_id,
                    )
                )
                .join(
                    TrafficDataTable,
                    TrafficDataTable.data_id == TrafficInstanceTable.data_id
                )
            )
            return readings

    @db_query
    def get_data_config(self, start_time: str = None, end_time: str = None, detectors: list = None, nweeks: int = None):
        """
        Get the data id and config from the TrafficDataTable.
        """
        # detectors = set(detectors)
        with self.dbcnxn.open_session() as session:
            readings = session.query(TrafficDataTable)
            if detectors:
                # filter by detector in the json field
                readings = readings.filter(
                    TrafficDataTable.data_config["detectors"].contained_by(
                        json.dumps(detectors)
                    )
                )

            if start_time:
                readings = readings.filter(
                    TrafficDataTable.data_config["start"].astext >= start_time
                )

            if end_time:
                readings = readings.filter(
                    TrafficDataTable.data_config["end"].astext <= end_time
                )

            if nweeks and nweeks > 1:
                readings = readings.filter(
                    and_(TrafficDataTable.data_config.has_key("nweeks"), TrafficDataTable.data_config["nweeks"].astext.cast(Integer) == nweeks)
                )
            else:
                # TODO: this is a temp fix whilst some data configs are missing nweeks. Remove this once data is backfilled.
                readings = readings.filter(
                    or_(
                        and_(
                            TrafficDataTable.data_config.has_key("nweeks"),
                            TrafficDataTable.data_config["nweeks"].astext.cast(Integer) == 1
                        ),
                        not_(TrafficDataTable.data_config.has_key("nweeks"))
                    )
                )

            return readings

    @db_query
    def get_instance_metrics(self, tag=None, data_ids=None, param_ids=None, models=None):
        """
        Get instances joined with the metrics.
        """
        instance_subquery = self.get_instances(tag=tag, data_ids=data_ids, param_ids=param_ids, models=models, output_type="subquery")
        with self.dbcnxn.open_session() as session:
            readings = session.query(TrafficMetric).join(instance_subquery, instance_subquery.c.instance_id == TrafficMetric.instance_id)
            return readings
