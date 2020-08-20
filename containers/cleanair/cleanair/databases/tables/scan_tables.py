"""Tables for Scoot scan statistics for the Odysseus project."""

import uuid
from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from ..base import Base


class FishnetTable(Base):
    """Grid/fishnet cast over a borough or other polygon.

    Notes:
        The primary key is (grid_resolution, row, col, borough).
    """

    __tablename__ = "fishnet"
    __table_args__ = {"schema": "traffic_modelling"}

    point_id = Column(
        UUID(as_uuid=True),
        primary_key=False,
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )
    grid_resolution = Column(Integer, primary_key=True, nullable=False, index=True)
    row = Column(Integer, nullable=False, primary_key=True)  # index starts at 1
    col = Column(Integer, nullable=False, primary_key=True)  # index starts at 1
    # note borough should be a foreign key to the london_boundary table
    # but because london_boundary doesn't have a unique attribute on
    # the name of a borough we can't create the foreign key
    # see issue: https://github.com/alan-turing-institute/clean-air-infrastructure/issues/465
    # borough = Column(String, ForeignKey("static_data.london_boundary.name"), nullable=False)
    borough = Column(String, primary_key=True, nullable=False, index=True)
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
    )
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    point_id = Column(
        UUID(as_uuid=True), ForeignKey(FishnetTable.point_id), primary_key=True
    )
    ebp = Column(DOUBLE_PRECISION, nullable=True)
    ebp_lower = Column(DOUBLE_PRECISION, nullable=True)
    ebp_upper = Column(DOUBLE_PRECISION, nullable=True)
    kulldorf_lower = Column(DOUBLE_PRECISION, nullable=True)
    kulldorf = Column(DOUBLE_PRECISION, nullable=True)
    kulldorf_upper = Column(DOUBLE_PRECISION, nullable=True)
    ebp_asym_lower = Column(DOUBLE_PRECISION, nullable=True)
    ebp_asym = Column(DOUBLE_PRECISION, nullable=True)
    ebp_asym_upper = Column(DOUBLE_PRECISION, nullable=True)
