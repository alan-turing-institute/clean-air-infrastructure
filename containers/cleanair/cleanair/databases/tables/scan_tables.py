"""Tables for Scoot scan statistics for the Odysseus project."""

import uuid
from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from ..base import Base


class Fishnet(Base):
    """Grid/fishnet cast over a borough or other polygon."""

    __tablename__ = "fishnet"
    __table_args__ = {"schema": "traffic_modelling"}

    # TODO once we've decided upon grid resolution this should have a
    # foreign key to the meta point table
    point_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    # note borough should be a foreign key to the london_boundary table
    # but because london_boundary doesn't have a unique attribute on
    # the name of a borough we can't create the foreign key
    # see issue: https://github.com/alan-turing-institute/clean-air-infrastructure/issues/465
    # borough = Column(String, ForeignKey("static_data.london_boundary.name"), nullable=False)
    borough = Column(String, nullable=False, index=True)
    geom = Column(
        Geometry(geometry_type="POLYGON", srid=4326, dimension=2, spatial_index=True),
        nullable=False,
    )


class ScootScanStats(Base):
    """Table of scoot scan statistics."""

    __tablename__ = "scoot_scan_stats"
    __table_args__ = {"schema": "traffic_modelling"}

    measurement_start_utc = Column(
        TIMESTAMP, primary_key=True, nullable=False, index=True
    )  # TIMESTAMP
    measurement_end_utc = Column(
        TIMESTAMP, primary_key=True, nullable=False
    )  # TIMESTAMP
    # TODO create id of grid
    point_id = Column(UUID(as_uuid=True), ForeignKey(Fishnet.point_id), primary_key=True)
    ebp_lower = Column(DOUBLE_PRECISION)
    ebp_upper = Column(DOUBLE_PRECISION)
    # TODO create columns for other metrics
