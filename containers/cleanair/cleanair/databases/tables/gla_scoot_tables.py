"""
Tables for GLA lockdown scoot
"""
from sqlalchemy import Column, ForeignKey, String, Integer, Enum
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from ..base import Base


class ScootPercentChange(Base):
    """Table of LAQN sites"""

    __tablename__ = "scoot_percentage_change"
    __table_args__ = {"schema": "gla_traffic"}

    detector_id = Column(
        String(9),
        ForeignKey("interest_points.scoot_detector.detector_n"),
        primary_key=True,
        nullable=False,
    )
    latest_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    latest_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    day_of_week = Column(Integer(), nullable=False)
    baseline_period = Column(
        Enum("lockdown", "normal", name="baseline_period_enum"),
        primary_key=True,
        nullable=False,
    )
    baseline_n_vehicles_in_interval = Column(Integer(), nullable=False)
    latest_n_vehicles_in_interval = Column(Integer(), nullable=False)
    percent_of_baseline = Column(DOUBLE_PRECISION(), nullable=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ScootPercentChange(" + ", ".join(vals) + ")>"
