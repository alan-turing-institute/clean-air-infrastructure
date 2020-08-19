"""Air quality forecast database queries and external api calls"""
from datetime import datetime
import logging
from typing import Optional, List, Tuple
from cachetools import cached, LRUCache, TTLCache
from cachetools.keys import hashkey
from sqlalchemy import func
from sqlalchemy.orm import Session, Query
from cleanair.databases.tables import (
    AirQualityInstanceTable,
    AirQualityResultTable,
    HexGrid,
)
from cleanair.decorators import db_query
from ..database import all_or_404


logger = logging.getLogger("fastapi") # pylint: disable=invalid-name


@db_query
def query_available_instance_ids(
    db: Session, start_datetime: datetime, end_datetime: datetime,
) -> Query:
    """
    Check which model IDs produced forecasts between start_datetime and end_datetime.
    """
    res = (
        db.query(
            AirQualityResultTable.instance_id,
            AirQualityResultTable.measurement_start_utc,
        )
        .join(
            AirQualityInstanceTable,
            AirQualityInstanceTable.instance_id == AirQualityResultTable.instance_id,
        )
        .filter(
            AirQualityInstanceTable.tag == "production",
            AirQualityInstanceTable.model_name == "svgp",
            AirQualityResultTable.measurement_start_utc >= start_datetime,
            AirQualityResultTable.measurement_start_utc <= end_datetime,
        )
    )

    # Return only instance IDs and distinct values
    res = res.with_entities(
        AirQualityInstanceTable.instance_id, AirQualityInstanceTable.fit_start_time
    ).distinct()

    # Order by fit start time
    return res.order_by(AirQualityInstanceTable.fit_start_time.desc())


@cached(
    cache=TTLCache(maxsize=256, ttl=60),
    key=lambda _, *args, **kwargs: hashkey(*args, **kwargs),
)
def cachable_available_instance_ids(
    db: Session, start_datetime: datetime, end_datetime: datetime,
) -> Optional[List[Tuple]]:
    """Cache results of query_available_instance_ids"""
    logger.info(
        "Querying available instance IDs between %s and %s",
        start_datetime, end_datetime
    )
    return query_available_instance_ids(db, start_datetime, end_datetime).all()


@db_query
def query_forecasts_nogeom(
    db: Session, instance_id: str, start_datetime: datetime, end_datetime: datetime
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


@cached(
    cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs)
)
def cachable_forecasts_nogeom(
    db: Session, instance_id: str, start_datetime: datetime, end_datetime: datetime,
) -> Optional[List[Tuple]]:
    """Cache results of query_forecasts_nogeom"""
    logger.info(
        "Querying forecasts for %s between %s and %s",
        instance_id, start_datetime, end_datetime
    )
    query = query_forecasts_nogeom(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
    return all_or_404(query)


@db_query
def query_forecasts_hexgrid(
    db: Session, instance_id: str, start_datetime: datetime, end_datetime: datetime
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
            func.ST_AsText(HexGrid.geom).label("geom"),
        )
        .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
        .filter(
            AirQualityResultTable.instance_id == instance_id,
            AirQualityResultTable.measurement_start_utc >= start_datetime,
            AirQualityResultTable.measurement_start_utc <= end_datetime,
        )
    )


@cached(
    cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs)
)
def cachable_forecasts_hexgrid(
    db: Session, instance_id: str, start_datetime: datetime, end_datetime: datetime,
) -> Optional[List[Tuple]]:
    """Cache results of query_forecasts_hexgrid"""
    logger.info(
        "Querying forecast geometries for %s between %s and %s",
        instance_id, start_datetime, end_datetime
    )
    query = query_forecasts_hexgrid(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
    return all_or_404(query)
