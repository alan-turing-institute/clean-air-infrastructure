"""
Tables for model results
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from ..base import Base


class ResultTable(Base):
    """Table of AQE sites"""

    __tablename__ = "result"
    __table_args__ = {"schema": "model_results"}

    instance_id = Column(
        String(64),
        ForeignKey("model_results.instance.instance_id"),
        primary_key=True,
        nullable=False,
    )
    point_id = Column(
        UUID,
        ForeignKey("interest_points.meta_point.id"),
        primary_key=True,
        nullable=False,
    )
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    # for each pollutant
    NO2_mean = Column(DOUBLE_PRECISION, nullable=True)
    NO2_var = Column(DOUBLE_PRECISION, nullable=True)
    PM10_mean = Column(DOUBLE_PRECISION, nullable=True)
    PM10_var = Column(DOUBLE_PRECISION, nullable=True)
    PM25_mean = Column(DOUBLE_PRECISION, nullable=True)
    PM25_var = Column(DOUBLE_PRECISION, nullable=True)
    CO2_mean = Column(DOUBLE_PRECISION, nullable=True)
    CO2_var = Column(DOUBLE_PRECISION, nullable=True)
    O3_mean = Column(DOUBLE_PRECISION, nullable=True)
    O3_var = Column(DOUBLE_PRECISION, nullable=True) 


    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ModelResults(" + ", ".join(vals)