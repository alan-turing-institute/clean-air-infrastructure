"""Mixin query for traffic data config."""

import json
from sqlalchemy import Integer
from cleanair.decorators import db_query
from ..tables import TrafficDataTable


class TrafficDataQueryMixin:
    """Queries for the traffic data table."""

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