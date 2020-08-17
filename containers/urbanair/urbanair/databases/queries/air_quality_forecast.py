"""Air quality forecast database queries and external api calls"""
from typing import Optional
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session, Query
from fastapi import HTTPException
from cleanair.databases.tables import (
    AirQualityInstanceTable,
    AirQualityResultTable,
    AirQualityDataTable,
    HexGrid,
    MetaPoint,
)
from cleanair.decorators import db_query
from cleanair.types import Source


@db_query
def get_available_instance_ids(
    db: Session, start_datetime: datetime, end_datetime: datetime,
) -> Query:
    """
    Check what forecast data is available between startdate and enddate.
    If startdate and enddate are not provided checks all availability.
    """
    res = db.query(
        AirQualityResultTable.instance_id,
        AirQualityResultTable.measurement_start_utc,
    ).join(
        AirQualityInstanceTable,
        AirQualityInstanceTable.instance_id == AirQualityResultTable.instance_id,
    ).filter(
        AirQualityInstanceTable.tag == "production",
        AirQualityInstanceTable.model_name == "svgp",
        AirQualityResultTable.measurement_start_utc >= start_datetime,
        AirQualityResultTable.measurement_start_utc <= end_datetime
    )

    # Return only instance IDs and distinct values
    res = res.with_entities(
        AirQualityInstanceTable.instance_id,
        AirQualityInstanceTable.fit_start_time
    ).distinct()

    # Order by fit start time
    return res.order_by(AirQualityInstanceTable.fit_start_time.desc())


@db_query
def get_forecasts(
    db: Session,
    instance_id: str,
    start_datetime: datetime,
    end_datetime: datetime
) -> Query:
    """
    Get all forecasts for a given model instance in the given datetime range
    """
    return (
        db.query(
            AirQualityResultTable.point_id,
            AirQualityResultTable.measurement_start_utc,
            AirQualityResultTable.NO2_mean,
            AirQualityResultTable.NO2_var,
        )
        .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
        .filter(
            AirQualityResultTable.instance_id == instance_id,
            AirQualityResultTable.measurement_start_utc >= start_datetime,
            AirQualityResultTable.measurement_start_utc <= end_datetime,
        )
        .filter(HexGrid.point_id == "15991a54-6330-455e-b220-6f397f56c777") # TODO remove
    )


@db_query
def get_forecasts_with_location(
    db: Session,
    instance_id: str,
    start_datetime: datetime,
    end_datetime: datetime
) -> Query:
    """
    Get all forecasts for a given model instance in the given datetime range
    """
    return (
        db.query(
            AirQualityResultTable.point_id,
            AirQualityResultTable.measurement_start_utc,
            AirQualityResultTable.NO2_mean,
            AirQualityResultTable.NO2_var,
            func.ST_X(MetaPoint.location).label("latitude"),
            func.ST_Y(MetaPoint.location).label("longitude"),
        )
        .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
        .filter(
            AirQualityResultTable.instance_id == instance_id,
            AirQualityResultTable.measurement_start_utc >= start_datetime,
            AirQualityResultTable.measurement_start_utc <= end_datetime,
        )
        .filter(HexGrid.point_id == "15991a54-6330-455e-b220-6f397f56c777") # TODO remove
    )
