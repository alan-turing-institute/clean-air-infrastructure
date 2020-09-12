"""Mixin query for traffic metrics."""

from cleanair.decorators import db_query
from cleanair.mixins import InstanceQueryMixin
from cleanair.databases.tables import TrafficMetricTable


class TrafficMetricQueryMixin(InstanceQueryMixin):
    """Query the metrics of traffic models that have been evaluated."""

    @db_query()
    def get_instance_metrics(
        self, tag=None, data_ids=None, param_ids=None, models=None
    ):
        """
        Get instances joined with the metrics.
        """
        instance_subquery = self.get_instances_with_params(
            tag=tag,
            data_ids=data_ids,
            param_ids=param_ids,
            models=models,
            output_type="subquery",
        )
        with self.dbcnxn.open_session() as session:
            readings = session.query(
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
            ).join(
                instance_subquery,
                instance_subquery.c.instance_id == TrafficMetricTable.instance_id,
            )
            return readings
