"""Air quality forecast database queries and external api calls"""
import logging
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, Query

from cachetools import cached, LRUCache, TTLCache
from cachetools.keys import hashkey
from cleanair.databases.tables import (
    AirQualityInstanceTable,
    AirQualityResultTable,
    HexGrid,
)
from cleanair.decorators import db_query

from ..database import all_or_404
from ..schemas.air_quality_forecast import ForecastResultGeoJson, GeometryGeoJson

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name


@db_query()
def query_instance_ids(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
) -> Query:
    """
    Check which model IDs produced forecasts between start_datetime and end_datetime.
    """
    query = (
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
            AirQualityResultTable.measurement_start_utc < end_datetime,
        )
    )

    # Return only instance IDs and distinct values
    query = query.with_entities(
        AirQualityInstanceTable.instance_id, AirQualityInstanceTable.fit_start_time
    ).distinct()

    # Order by fit start time
    return query.order_by(AirQualityInstanceTable.fit_start_time.desc())


@cached(
    cache=TTLCache(maxsize=256, ttl=60),
    key=lambda _, *args, **kwargs: hashkey(*args, **kwargs),
)
def cached_instance_ids(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
) -> Optional[List[Tuple]]:
    """Cache available model instances"""
    logger.info(
        "Querying available instance IDs between %s and %s",
        start_datetime,
        end_datetime,
    )
    return query_instance_ids(db, start_datetime, end_datetime).all()


@db_query()
def query_geometries_hexgrid(
    db: Session,
    bounding_box: Optional[Tuple[float]] = None,
) -> Query:
    """
    Query geometries for combining with plain JSON forecasts
    """
    query = db.query(
        HexGrid.point_id,
        func.ST_AsText(func.ST_Transform(HexGrid.geom, 4326)).label("geom"),
    )
    # Note that SRID 4326 is not aligned with lat/lon so we return all geometries that
    # overlap with any part of the lat/lon bounding box
    if bounding_box:
        query = query.filter(
            func.ST_Intersects(HexGrid.geom, func.ST_MakeEnvelope(*bounding_box, 4326))
        )
    return query.distinct()


@cached(
    cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs)
)
def cached_geometries_hexgrid(
    db: Session,
    bounding_box: Optional[Tuple[float]] = None,
) -> GeometryGeoJson:
    """Cache geometries with optional bounding box"""
    logger.info("Querying hexgrid geometries")
    if bounding_box:
        logger.info("Restricting to bounding box (%s, %s => %s, %s)", *bounding_box)
    query_results = query_geometries_hexgrid(db, bounding_box=bounding_box)
    # Return the query results as a GeoJSON FeatureCollection
    features = GeometryGeoJson.build_features([r._asdict() for r in query_results])
    return GeometryGeoJson(features=features)


@db_query()
def query_forecasts_hexgrid(
    db: Session,
    instance_id: str,
    start_datetime: datetime,
    end_datetime: datetime,
    with_geometry: bool,
    bounding_box: Optional[Tuple[float]] = None,
) -> Query:
    """
    Get all forecasts for a given model instance in the given datetime range
    """
    if with_geometry:
        query = db.query(
            AirQualityResultTable.point_id,
            AirQualityResultTable.measurement_start_utc,
            func.nullif(AirQualityResultTable.NO2_mean, "NaN").label("NO2_mean"),
            func.nullif(AirQualityResultTable.NO2_var, "NaN").label("NO2_var"),
            func.ST_AsText(func.ST_Transform(HexGrid.geom, 4326)).label("geom"),
        )
    else:
        query = db.query(
            AirQualityResultTable.point_id,
            AirQualityResultTable.measurement_start_utc,
            func.nullif(AirQualityResultTable.NO2_mean, "NaN").label("NO2_mean"),
            func.nullif(AirQualityResultTable.NO2_var, "NaN").label("NO2_var"),
        )

    # Restrict to hexgrid points for the given instance and times
    query = query.join(
        HexGrid, HexGrid.point_id == AirQualityResultTable.point_id
    ).filter(
        AirQualityResultTable.instance_id == instance_id,
        AirQualityResultTable.measurement_start_utc >= start_datetime,
        AirQualityResultTable.measurement_start_utc < end_datetime,
    )

    # Note that SRID 4326 is not aligned with lat/lon so we return all geometries that
    # overlap with any part of the lat/lon bounding box
    if bounding_box:
        query = query.filter(
            func.ST_Intersects(HexGrid.geom, func.ST_MakeEnvelope(*bounding_box, 4326))
        )
    return query


@cached(
    cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs)
)
def cached_forecast_hexgrid_json(
    db: Session,
    instance_id: str,
    start_datetime: datetime,
    end_datetime: datetime,
    with_geometry: bool,
    bounding_box: Optional[Tuple[float]] = None,
) -> Optional[List[Tuple]]:
    """Cache forecasts with geometry with optional bounding box"""
    logger.info(
        "Querying forecast geometries for %s between %s and %s",
        instance_id,
        start_datetime,
        end_datetime,
    )
    if bounding_box:
        logger.info("Restricting to bounding box (%s, %s => %s, %s)", *bounding_box)
    query = query_forecasts_hexgrid(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=with_geometry,
        bounding_box=bounding_box,
    )
    return all_or_404(query)


@cached(
    cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs)
)
def cached_forecast_hexgrid_geojson(
    db: Session,
    instance_id: str,
    start_datetime: datetime,
    end_datetime: datetime,
    bounding_box: Optional[Tuple[float]] = None,
) -> ForecastResultGeoJson:
    """Cache forecasts with geometry with optional bounding box"""
    query_results = cached_forecast_hexgrid_json(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=True,
        bounding_box=bounding_box,
    )
    # Return the query results as a GeoJSON FeatureCollection
    features = ForecastResultGeoJson.build_features(
        [r._asdict() for r in query_results]
    )
    return ForecastResultGeoJson(features=features)
