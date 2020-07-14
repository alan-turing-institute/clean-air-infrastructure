"""Forecast database queries and external api calls"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql.selectable import Alias
from geojson import Feature, Point, FeatureCollection
import requests
from cleanair.databases.tables import AirQualityInstanceTable
from cleanair.decorators import db_query
from ...types import DetectionClass

TWELVE_HOUR_INTERVAL = text("interval '12 hour'")
ONE_HOUR_INTERVAL = text("interval '1 hour'")


def get_forecast_available(db: Session, limit: int = 100) -> Query:
    """Get instance data availability"""

    res = db.query(
        AirQualityInstanceTable.instance_id,
        AirQualityInstanceTable.fit_start_time,
        AirQualityInstanceTable.tag,
        AirQualityInstanceTable.model_name,
    )

    return res
