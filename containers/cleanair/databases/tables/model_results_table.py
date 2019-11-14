"""
Tables for model results
"""
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from ..base import Base


class ModelResult(Base):
    """Table of AQE sites"""
    __tablename__ = "model_results"
    __table_args__ = {"schema": "model_results"}

    fit_start_time = Column(TIMESTAMP, primary_key=True, nullable=False)
    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), nullable=False)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    predict_mean = Column(DOUBLE_PRECISION, nullable=False)
    predict_var = Column(DOUBLE_PRECISION, nullable=False)
