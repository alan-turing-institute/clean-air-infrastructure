"""Mixin query for traffic data config."""

import json
from typing import List, Optional
from cleanair.databases import Connector
from cleanair.decorators import db_query
from cleanair.databases.tables import TrafficDataTable


class ScootDataQueryMixin:
    """Queries for the traffic data table."""

    # necessary to stop mypy complaining during type hinting
    dbcnxn: Connector

    @db_query()
    def scoot_config(
        self,
        start: Optional[str] = None,
        upto: Optional[str] = None,
        detectors: Optional[List[str]] = None,
    ):
        """Get the data id and config from the Scoot data config table."""
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

            if start:
                readings = readings.filter(
                    TrafficDataTable.data_config["start"].astext >= start
                )

            if upto:
                readings = readings.filter(
                    TrafficDataTable.data_config["upto"].astext < upto
                )
            return readings
