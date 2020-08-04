"""Forecast database queries and external api calls"""
from typing import Optional
from datetime import date
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
def get_forecast_available(
    db: Session, startdate: Optional[date], enddate: Optional[date],
) -> Query:
    """Check what forecast data is available between startdate and enddate.
    If startdate and enddate are not provided checks all availability"""

    res = db.query(
        AirQualityInstanceTable.instance_id,
        AirQualityInstanceTable.fit_start_time,
        AirQualityInstanceTable.tag,
        AirQualityInstanceTable.model_name,
    ).join(
        AirQualityDataTable,
        AirQualityInstanceTable.data_id == AirQualityDataTable.data_id,
    )

    # Filter by source
    res = res.filter(
        AirQualityDataTable.data_config["pred_sources"].astext.contains(
            Source.hexgrid.value
        )
    )

    # Filter by time
    if startdate:
        res = res.filter(AirQualityInstanceTable.fit_start_time >= startdate,)
    if enddate:
        res = res.filter(AirQualityInstanceTable.fit_start_time < enddate)

    # Order by fit start time
    return res.order_by(AirQualityInstanceTable.fit_start_time)


@db_query
def get_forecast(db: Session, instance_id: Optional[str]) -> Query:
    """Get instance model results"""

    return (
        db.query(
            AirQualityResultTable.point_id,
            AirQualityResultTable.measurement_start_utc,
            AirQualityResultTable.NO2_mean,
            AirQualityResultTable.NO2_var,
            func.ST_GeometryN(HexGrid.geom, 1).label("geom"),
        )
        .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
        .filter(AirQualityResultTable.instance_id == instance_id)
    )


@db_query
def get_forecast_json(db: Session, instance_id: str,) -> Query:
    """Get instance model geojson results"""

    out_sq = get_forecast(db, instance_id, output_type="subquery")

    out = db.query(
        func.jsonb_build_object(
            "id",
            out_sq.c.point_id,
            "geometry",
            func.ST_AsGeoJSON(out_sq.c.geom),
            "properties",
            func.jsonb_build_object(
                "measurement_start_utc",
                out_sq.c.measurement_start_utc,
                "NO2_mean",
                out_sq.c.NO2_mean,
                "NO2_var",
                out_sq.c.NO2_var,
            ),
        )
    )

    return out
