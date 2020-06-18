"""Tables for air quality instances, models, data, metrics and results."""

from sqlalchemy import ForeignKeyConstraint, Column
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from ..base import Base
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


class AirQualityMetricsTable(Base, MetricsTableMixin):
    """Storing metrics that have been evaluated on a model."""

    __tablename__ = "air_quality_metrics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["air_quality_modelling.air_quality_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["instance_id"], ["air_quality_modelling.air_quality_instance.instance_id"]
        ),
        {"schema": "air_quality_modelling"},
    )

    # columns for NO2 metrics
    NO2_mae = Column(DOUBLE_PRECISION, nullable=True, index=False)
    NO2_mse = Column(DOUBLE_PRECISION, nullable=True, index=False)
    NO2_r2_score = Column(DOUBLE_PRECISION, nullable=False, index=False)

    # columns for O3 metrics
    O3_mae = Column(DOUBLE_PRECISION, nullable=True, index=False)
    O3_mse = Column(DOUBLE_PRECISION, nullable=True, index=False)
    O3_r2_score = Column(DOUBLE_PRECISION, nullable=True, index=False)

    # columns for PM10 metrics
    PM10_mae = Column(DOUBLE_PRECISION, nullable=True, index=False)
    PM10_mse = Column(DOUBLE_PRECISION, nullable=True, index=False)
    PM10_r2_score = Column(DOUBLE_PRECISION, nullable=True, index=False)

    # columns for PM25 metrics
    PM25_mae = Column(DOUBLE_PRECISION, nullable=True, index=False)
    PM25_mse = Column(DOUBLE_PRECISION, nullable=True, index=False)
    PM25_r2_score = Column(DOUBLE_PRECISION, nullable=True, index=False)

    # columns for CO2 metrics
    CO2_mae = Column(DOUBLE_PRECISION, nullable=True, index=False)
    CO2_mse = Column(DOUBLE_PRECISION, nullable=True, index=False)
    CO2_r2_score = Column(DOUBLE_PRECISION, nullable=True, index=False)


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
