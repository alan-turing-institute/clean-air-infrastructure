"""
Tables for model results
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from ..base import Base


class ModelResult(Base):
    """Table of AQE sites"""
    __tablename__ = "model_results"
    __table_args__ = {"schema": "model_results"}

    fit_time = Column(TIMESTAMP, primary_key=True, nullable=False)
    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), nullable=False)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    predict_mean = Column(DOUBLE_PRECISION, nullable=False)
    predict_var = Column(DOUBLE_PRECISION, nullable=False)


    @staticmethod
    def build_entry(fit_time, point_id, measurement_start_utc, measurement_end_utc, predict_mean, predict_var):
        """Create an ModelResult entry"""

        # Construct the record and return it
        return ModelResult(fit_time, point_id, measurement_start_utc, measurement_end_utc, predict_mean, predict_var)