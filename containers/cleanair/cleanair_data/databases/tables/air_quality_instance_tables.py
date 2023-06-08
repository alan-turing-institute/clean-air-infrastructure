"""Tables for air quality instances, models, data, metrics and results."""

from sqlalchemy import ForeignKeyConstraint, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, UUID, TIMESTAMP, BOOLEAN
from ..base import Base
from .meta_point_table import MetaPoint
from ..mixins.instance_tables_mixin import (
    InstanceTableMixin,
    ModelTableMixin,
    DataTableMixin,
    MetricsTableMixin,
    ResultTableMixin,
)


class AirQualityInstanceTable(Base, InstanceTableMixin):
    """Store a air quality instance."""

    __tablename__ = "air_quality_instance"

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["air_quality_modelling.air_quality_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["model_name", "param_id"],
            [
                "air_quality_modelling.air_quality_model.model_name",
                "air_quality_modelling.air_quality_model.param_id",
            ],
        ),
        {"schema": "air_quality_modelling"},
    )


class AirQualityDataTable(Base, DataTableMixin):
    """Storing settings for air quality data settings."""

    __tablename__ = "air_quality_data"
    __table_args__ = {"schema": "air_quality_modelling"}


class AirQualityModelTable(Base, ModelTableMixin):
    """Store model parameters for an air qualty instance."""

    __tablename__ = "air_quality_model"
    __table_args__ = {"schema": "air_quality_modelling"}


class AirQualitySpatialMetricsTable(Base, MetricsTableMixin):
    """Storing metrics for each sensor that have been evaluated on a model."""

    __tablename__ = "spatial_metrics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["air_quality_modelling.air_quality_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["instance_id"], ["air_quality_modelling.air_quality_instance.instance_id"]
        ),
        {"schema": "air_quality_modelling"},
    )
    point_id = Column(UUID, ForeignKey(MetaPoint.id), primary_key=True)
    forecast = Column(
        BOOLEAN, primary_key=True
    )  # if true the metrics are evaluated on forecasts
    source = Column(String(20), primary_key=True)
    pollutant = Column(String(4), primary_key=True)

    # columns for metrics
    mae = Column(DOUBLE_PRECISION, nullable=False, index=False)
    mse = Column(DOUBLE_PRECISION, nullable=False, index=False)
    r2_score = Column(DOUBLE_PRECISION, nullable=False, index=False)


class AirQualityTemporalMetricsTable(Base, MetricsTableMixin):
    """Metrics for each timestamp aggregated over all sensors."""

    __tablename__ = "temporal_metrics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["air_quality_modelling.air_quality_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["instance_id"], ["air_quality_modelling.air_quality_instance.instance_id"]
        ),
        {"schema": "air_quality_modelling"},
    )
    forecast = Column(
        BOOLEAN, primary_key=True
    )  # if true the metrics are evaluated on forecasts
    source = Column(String(20), primary_key=True)
    pollutant = Column(String(4), primary_key=True)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=False, nullable=False)

    # columns for metrics
    mae = Column(DOUBLE_PRECISION, nullable=False, index=False)
    mse = Column(DOUBLE_PRECISION, nullable=False, index=False)
    r2_score = Column(DOUBLE_PRECISION, nullable=False, index=False)


class AirQualityResultTable(Base, ResultTableMixin):
    """Storing the results of air quality model fits."""

    __tablename__ = "air_quality_result"

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["air_quality_modelling.air_quality_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["instance_id"], ["air_quality_modelling.air_quality_instance.instance_id"]
        ),
        ForeignKeyConstraint(["point_id"], ["interest_points.meta_point.id"]),
        {"schema": "air_quality_modelling"},
    )

    # column for each pollutant
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
