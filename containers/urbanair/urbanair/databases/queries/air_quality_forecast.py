"""Air quality forecast database queries and external api calls"""
from cachetools import cached, LRUCache
from cachetools.keys import hashkey
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, Query
from cleanair.databases.tables import (
    AirQualityInstanceTable,
    AirQualityResultTable,
    HexGrid,
    MetaPoint,
)
from cleanair.decorators import db_query
from ..database import all_or_404


@db_query
def query_available_instance_ids(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
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


@cached(cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs))
def cachable_available_instance_ids(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
) -> Optional[List[Tuple]]:
    return query_available_instance_ids(db, start_datetime, end_datetime).all()


@db_query
def query_forecasts(
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
    )


@cached(cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs))
def cachable_forecasts(
    db: Session,
    instance_id: str,
    start_datetime: datetime,
    end_datetime: datetime,
) -> Optional[List[Tuple]]:
    query = query_forecasts(db, instance_id=instance_id, start_datetime=start_datetime, end_datetime=end_datetime)
    return all_or_404(query)


@db_query
def query_forecasts_with_location(
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
            func.ST_AsText(MetaPoint.location).label("location"),
        )
        .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
        .join(MetaPoint, MetaPoint.id == HexGrid.point_id)
        .filter(
            AirQualityResultTable.instance_id == instance_id,
            AirQualityResultTable.measurement_start_utc >= start_datetime,
            AirQualityResultTable.measurement_start_utc <= end_datetime,
        )
    )


@cached(cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs))
def cachable_forecasts_with_location(
    db: Session,
    instance_id: str,
    start_datetime: datetime,
    end_datetime: datetime,
) -> Optional[List[Tuple]]:
    query = query_forecasts_with_location(db, instance_id=instance_id, start_datetime=start_datetime, end_datetime=end_datetime)
    return all_or_404(query)
