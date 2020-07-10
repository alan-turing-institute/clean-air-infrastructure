"""Class for scan stats interacting with DB."""

from sqlalchemy import func
from cleanair.databases import DBReader
from cleanair.databases.tables import MetaPoint, ScootDetector, ScootReading
from cleanair.decorators import db_query
from cleanair.mixins import ScootQueryMixin
from ..databases.mixins import GridMixin

class ScanScoot(GridMixin, ScootQueryMixin, DBReader):
    """Reading and writing scan stats for SCOOT."""

    @db_query
    def scoot_fishnet(self, borough: str):
        """Get a grid over a borough and join on scoot detectors."""
        fishnet = self.fishnet_over_borough(borough, output_type="subquery")
        detectors = self.get_scoot_detectors(output_type="subquery")
        with self.dbcnxn.open_session() as session:
            readings = session.query(
                fishnet,
                detectors
            ).join(detectors, func.ST_Intersects(fishnet.geom, detectors.geom))
            return readings

    @db_query
    def scoot_fishnet_readings(self, borough: str):
        """Get a grid over a borough and return all scoot readings in that grid."""
        fishnet = self.scoot_fishnet(borough, output_type="subquery")
        with self.dbcnxn.open_session() as session:
            readings = session.query(ScootReading, fishnet).join(
                fishnet, ScootReading.detector_id == fishnet.detector_id
            )
