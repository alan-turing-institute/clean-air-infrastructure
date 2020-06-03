"""
Tables for GLA lockdown scoot
"""
from sqlalchemy import Column, ForeignKey, String, Integer, Enum
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, BOOLEAN
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
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    day_of_week = Column(Integer(), nullable=False)
    baseline_period = Column(
        Enum("lockdown", "normal", name="baseline_period_enum"),
        primary_key=True,
        nullable=False,
    )
    baseline_start_date = Column(TIMESTAMP, primary_key=True, nullable=False)
    baseline_end_date = Column(TIMESTAMP, primary_key=True, nullable=False)
    baseline_n_vehicles_in_interval = Column(Integer(), nullable=False)
    # pylint: disable=C0103
    comparison_n_vehicles_in_interval = Column(Integer(), nullable=False)
    # pylint: enable=C0103
    percent_of_baseline = Column(DOUBLE_PRECISION(), nullable=False)
    no_traffic_in_baseline = Column(BOOLEAN, nullable=False)
    no_traffic_in_comparison = Column(BOOLEAN, nullable=False)
    low_confidence = Column(BOOLEAN, nullable=False)
    num_observations = Column(Integer, nullable=False)
    removed_anomaly_from_baseline = Column(BOOLEAN, nullable=False)
    removed_anomaly_from_comparison = Column(BOOLEAN, nullable=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ScootPercentChange(" + ", ".join(vals) + ")>"
