"""
Class for querying traffic and scoot data.
"""

import json
from sqlalchemy import and_, Integer
from cleanair.databases import DBReader
from cleanair.mixins import ScootQueryMixin
from cleanair.decorators import db_query
from .tables import TrafficInstanceTable, TrafficModelTable, TrafficDataTable, TrafficMetricTable

class TrafficQuery(DBReader, ScootQueryMixin):
    """Query traffic data."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)

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
        models: list = None,
        fit_start_time: str = None,
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
            # get all instances that were fit after the given date
            if fit_start_time:
                readings = readings.filter(
                    TrafficInstanceTable.fit_start_time > fit_start_time
                )
            return readings

    @db_query
    def get_instances_with_params(
        self,
        tag: str = None,
        instance_ids: list = None,
        data_ids: list = None,
        param_ids: list = None,
        models: list = None,
        fit_start_time: str = None,
    ):
        """
        Get all traffic instances and join the json parameters.
        """
        instance_subquery = self.get_instances(
            tag=tag, instance_ids=instance_ids, data_ids=data_ids,
            param_ids=param_ids, models=models, fit_start_time=fit_start_time,
            output_type="subquery")
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
                        TrafficModelTable.model_name == instance_subquery.c.model_name,
                        TrafficModelTable.param_id == instance_subquery.c.param_id,
                    )
                )
                .join(
                    TrafficDataTable,
                    TrafficDataTable.data_id == instance_subquery.c.data_id
                )
            )
            return readings

    @db_query
    def get_data_config(
        self,
        start_time: str = None,
        end_time: str = None,
        detectors: list = None,
        nweeks: int = None,
        baseline_period: str = None,
    ):
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
                # TODO: should this be strictly less than?
                readings = readings.filter(
                    TrafficDataTable.data_config["end"].astext <= end_time
                )

            if nweeks:
                # TODO: the below method is not working due to casting problem (nweeks field is float/string not int)
                readings = readings.filter(
                    TrafficDataTable.data_config["nweeks"].astext.cast(Integer) == nweeks
                )

            if baseline_period:
                readings = readings.filter(
                    TrafficDataTable.data_config["baseline_period"].astext == baseline_period
                )

            return readings

    @db_query
    def get_instance_metrics(self, tag=None, data_ids=None, param_ids=None, models=None):
        """
        Get instances joined with the metrics.
        """
        instance_subquery = self.get_instances_with_params(
            tag=tag,
            data_ids=data_ids,
            param_ids=param_ids,
            models=models,
            output_type="subquery"
        )
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(
                    TrafficMetricTable.instance_id,
                    TrafficMetricTable.coverage50,
                    TrafficMetricTable.coverage75,
                    TrafficMetricTable.coverage95,
                    TrafficMetricTable.nlpl,
                    instance_subquery.c.model_name,
                    instance_subquery.c.param_id,
                    instance_subquery.c.data_id,
                    instance_subquery.c.cluster_id,
                    instance_subquery.c.tag,
                    instance_subquery.c.fit_start_time,
                    instance_subquery.c.git_hash,
                    instance_subquery.c.model_param,
                    instance_subquery.c.data_config,
                )
                .join(instance_subquery, instance_subquery.c.instance_id == TrafficMetricTable.instance_id)
            )
            return readings
