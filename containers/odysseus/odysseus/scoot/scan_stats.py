"""Class for scan stats interacting with DB."""

from typing import Optional
from sqlalchemy import func
from cleanair.databases import DBReader
from cleanair.decorators import db_query
from cleanair.mixins import ScootQueryMixin
from ..databases.mixins import GridMixin


class ScanScoot(GridMixin, ScootQueryMixin, DBReader):
    """Reading and writing scan stats for SCOOT."""

    @db_query
    def scoot_fishnet(self, borough: str):
        """Get a grid over a borough and join on scoot detectors.

        Args:
            borough: The name of the borough to get scoot detectors for.

        Notes:
            The geometry column of the scoot detector table is renamed to 'location'.
            The geometry column of the fishnet is 'geom'.
        """
        # TODO add xmin, ymin, xmax, ymax for each grid square
        fishnet = self.fishnet_over_borough(borough, output_type="subquery")
        detectors = self.get_scoot_detectors(
            output_type="subquery", geom_label="location"
        )
        with self.dbcnxn.open_session() as session:
            readings = session.query(detectors, fishnet).join(
                fishnet, func.ST_Intersects(fishnet.c.geom, detectors.c.location)
            )
            return readings

    @db_query
    def scoot_fishnet_readings(
        self, borough: str, start_time: str, end_time: Optional[str] = None,
    ):
        """Get a grid over a borough and return all scoot readings in that grid."""
        fishnet = self.scoot_fishnet(borough, output_type="subquery")
        readings = self.scoot_readings(
            start_time=start_time,
            end_time=end_time,
            detectors=fishnet.detector_id,
            with_location=False,
            output_type="subquery",
        )
        with self.dbcnxn.open_session() as session:
            return session.query(readings).join(
                fishnet, readings.detector_id == fishnet.detector_id
            )
