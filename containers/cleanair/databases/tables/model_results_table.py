"""
Tables for model results
"""
from sqlalchemy import Column, ForeignKey, String, Index, select, func
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.ext.declarative import DeferredReflection
from .meta_point_table import MetaPoint
from ..base import Base, create_mat_view


class ModelResult(Base):
    """Table of AQE sites"""

    __tablename__ = "model_results"
    __table_args__ = {"schema": "model_results"}

    tag = Column(String(32), nullable=False)
    fit_start_time = Column(TIMESTAMP, primary_key=True, nullable=False)
    point_id = Column(
        UUID,
        ForeignKey("interest_points.meta_point.id"),
        primary_key=True,
        nullable=False,
    )
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    predict_mean = Column(DOUBLE_PRECISION, nullable=False)
    predict_var = Column(DOUBLE_PRECISION, nullable=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ModelResults(" + ", ".join(vals)


def APIForecastView():
    """Get a selectable for a materialized view for the API Forecast
    Get the latest production forecast"""
    interest_point_sq = select([MetaPoint.location,
                                func.ST_X(MetaPoint.location).label("lon"),
                                func.ST_Y(MetaPoint.location).label("lat"),
                                MetaPoint.id]).where(MetaPoint.source == "grid_100").alias('interest_points')

    latest_model_fit = select([func.max(ModelResult.fit_start_time).label("latest_forecast")]).alias("latest_forecast")

    mrv_select = select([interest_point_sq.c.id,
                         interest_point_sq.c.lon,
                         interest_point_sq.c.lat,
                         ModelResult.measurement_start_utc,
                         ModelResult.predict_mean,
                         ModelResult.predict_var]).select_from(interest_point_sq.join(ModelResult)).where(
        ModelResult.fit_start_time == latest_model_fit.c.latest_forecast)

    return mrv_select


class ModelResultsView(Base):
    """Test model results view"""

    __tablename__ = "api_forecast"
    __table_args__ = {"schema": "model_results"}
    __table__ = create_mat_view(Base.metadata,
                                "{}.{}".format(__table_args__['schema'], __tablename__),
                                APIForecastView()
                                )
