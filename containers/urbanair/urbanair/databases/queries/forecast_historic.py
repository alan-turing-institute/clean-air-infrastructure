"""Forecast database queries and external api calls"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import func, text
import geopandas as gpd
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql.selectable import Alias
from geojson import Feature, Point, FeatureCollection
import requests
from cleanair.databases.tables import AirQualityInstanceTable, AirQualityResultTable, MetaPoint, HexGrid
from cleanair.decorators import db_query
from ...types import DetectionClass


TWELVE_HOUR_INTERVAL = text("interval '12 hour'")
ONE_HOUR_INTERVAL = text("interval '1 hour'")

def instance_id_filter(query: Query, instance_id: Optional[str]) -> Query:
    "Filter by instance_id"
    if instance_id:
        return query.filter( AirQualityResultTable.instance_id == instance_id)
    return query

def get_forecast_values(db: Session) -> Query:
    """Get instance data availability"""

    res = db.query(
        AirQualityInstanceTable.instance_id,
        AirQualityInstanceTable.fit_start_time,
        AirQualityInstanceTable.tag,
        AirQualityInstanceTable.model_name,
    )

    return res


def get_forecast_available(
    db: Session,
    starttime: Optional[datetime] ,
    endtime: Optional[datetime] ,
    
) -> Query:
    """Check what forecast data is available between starttime and endtime.
    If starttime and endtime are not provided checks all availability"""
    
    res = db.query(
        AirQualityInstanceTable.instance_id,
        AirQualityInstanceTable.fit_start_time,
        AirQualityInstanceTable.tag,
        AirQualityInstanceTable.model_name,
    )

    # Filter by time
    if starttime:
        res = res.filter(AirQualityInstanceTable.fit_start_time >= starttime,)
    if endtime:
        res = res.filter(AirQualityInstanceTable.fit_start_time < endtime)

    return res


def get_forecast_resultValues(db: Session, instance_id: Optional[str],limit: int = 100) -> Query:
    """Get instance model results"""

    res = db.query(
        AirQualityResultTable.instance_id,
        AirQualityResultTable.data_id,
        AirQualityResultTable.point_id,
        AirQualityResultTable.measurement_start_utc,
        AirQualityResultTable.NO2_mean
    )

    # Filter by instance_id
    res = instance_id_filter(res, instance_id).limit(limit)


    return res


def get_forecast_json(db: Session, instance_id:str, limit: int = 100)-> Query:

    out_sq = (
        db.query(
            AirQualityResultTable.point_id,
            AirQualityResultTable.measurement_start_utc,
            AirQualityResultTable.NO2_mean,
            AirQualityResultTable.NO2_var,
            func.ST_GeometryN(HexGrid.geom, 1).label("geom")
        )
        .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
        .filter(AirQualityResultTable.instance_id == instance_id)
        .limit(limit)
           
    ).subquery()

    
    out = (
        db.query(
            func.jsonb_build_object(
                                    'id', out_sq.c.point_id, 
                                    'geometry',func.jsonb_build_object(
                                        'type',func.ST_GeometryType(out_sq.c.geom),
                                        'coordinates',func.ST_FlipCoordinates(out_sq.c.geom)),
                                    'properties', func.jsonb_build_object('measurement_start_utc', out_sq.c.measurement_start_utc, 
                                                                        'NO2_mean', out_sq.c.NO2_mean,
                                                                        'NO2_var', out_sq.c.NO2_var) )
        )
    )

    return out