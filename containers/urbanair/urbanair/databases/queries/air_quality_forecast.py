"""Air quality forecast database queries and external api calls"""
import logging
from time import time
from datetime import datetime, date
from typing import Optional, List, Tuple

from sqlalchemy import func, DATE
from sqlalchemy.orm import Session, Query

from cachetools import cached, LRUCache, TTLCache
from cachetools.keys import hashkey
from cleanair.databases.tables import (
    AirQualityInstanceTable,
    AirQualityResultTable,
    HexGrid,
    AirQualityDataTable,
)
from cleanair.decorators import db_query
from cleanair.params import PRODUCTION_STATIC_FEATURES, PRODUCTION_DYNAMIC_FEATURES
from cleanair.types import DynamicFeatureNames, StaticFeatureNames
from ..database import all_or_404
from ..schemas.air_quality_forecast import ForecastResultGeoJson, GeometryGeoJson

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name


@db_query()
def query_instance_ids(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
    static_features: List[StaticFeatureNames],
    dynamic_features: List[DynamicFeatureNames],
) -> Query:
    """
    Check which model IDs produced forecasts between start_datetime and end_datetime.
    """
    query = (
        db.query(
            AirQualityResultTable.instance_id,
            AirQualityResultTable.measurement_start_utc,
        )
        .filter(
            AirQualityResultTable.measurement_start_utc >= start_datetime,
            AirQualityResultTable.measurement_start_utc < end_datetime,
        )
        .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
        .join(
            AirQualityInstanceTable,
            AirQualityInstanceTable.instance_id == AirQualityResultTable.instance_id,
        )
        .filter(
            AirQualityInstanceTable.tag == "production",
            AirQualityInstanceTable.model_name == "mrdgp",
        )
        .join(
            AirQualityDataTable,
            AirQualityInstanceTable.data_id == AirQualityDataTable.data_id,
        )
        .filter(
            AirQualityDataTable.data_config["static_features"]
            == [feature.value for feature in static_features],
            AirQualityDataTable.data_config["dynamic_features"]
            == [feature.value for feature in dynamic_features],
        )
    )

    # Return only instance IDs and distinct values
    query = query.with_entities(
        AirQualityInstanceTable.instance_id, AirQualityInstanceTable.fit_start_time
    ).distinct()

    # Order by fit start time
    return query.order_by(AirQualityInstanceTable.fit_start_time.desc())


@db_query()
def query_instance_ids_on_date(
    db: Session,
    run_date: date,
    static_features: List[StaticFeatureNames],
    dynamic_features: List[DynamicFeatureNames],
) -> Query:
    """
    Check which model IDs produced forecasts on date.
    """
    query = (
        db.query(
            AirQualityInstanceTable.instance_id, AirQualityInstanceTable.fit_start_time,
        )
        .join(
            AirQualityDataTable,
            AirQualityInstanceTable.data_id == AirQualityDataTable.data_id,
        )
        .filter(
            func.cast(AirQualityInstanceTable.fit_start_time, DATE) == run_date,
            AirQualityInstanceTable.tag == "production",
            AirQualityInstanceTable.model_name == "mrdgp",
            AirQualityDataTable.data_config["static_features"]
            == [feature.value for feature in static_features],
            AirQualityDataTable.data_config["dynamic_features"]
            == [feature.value for feature in dynamic_features],
        )
    )

    # Order by fit start time
    return query.order_by(AirQualityInstanceTable.fit_start_time.desc())


@cached(
    cache=TTLCache(maxsize=256, ttl=2 * 60 * 60 * 24, timer=time),
    key=lambda _, *args, **kwargs: hashkey(*args, **kwargs),
)
def cached_instance_ids(
    db: Session, start_datetime: datetime, end_datetime: datetime,
) -> Optional[List[Tuple]]:
    """Cache available model instances that cover the datetime range"""
    logger.info(
        "Querying available instance IDs between %s and %s",
        start_datetime,
        end_datetime,
    )
    return query_instance_ids(
        db=db,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        static_features=PRODUCTION_STATIC_FEATURES,
        dynamic_features=PRODUCTION_DYNAMIC_FEATURES,
    ).all()


@cached(
    cache=TTLCache(maxsize=256, ttl=2 * 60 * 60 * 24, timer=time),
    key=lambda _, *args, **kwargs: hashkey(*args, **kwargs),
)
def cached_instance_ids_on_run_date(
    db: Session, run_date: date,
) -> Optional[List[Tuple]]:
    """Cache available model instances run on this date"""
    logger.info(
        "Querying available instance IDs on %s", run_date,
    )
    return query_instance_ids_on_date(
        db=db,
        run_date=run_date,
        static_features=PRODUCTION_STATIC_FEATURES,
        dynamic_features=PRODUCTION_DYNAMIC_FEATURES,
    ).all()


@db_query()
def query_geometries_hexgrid(
    db: Session, bounding_box: Optional[Tuple[float]] = None,
) -> Query:
    """
    Query geometries for combining with plain JSON forecasts
    """
    query = db.query(
        HexGrid.point_id,
        HexGrid.hex_id,
        func.ST_AsText(func.ST_Transform(HexGrid.geom, 4326)).label("geom"),
    )
    # Note that SRID 4326 is not aligned with lat/lon so we return all geometries that
    # overlap with any part of the lat/lon bounding box
    if bounding_box:
        query = query.filter(
            func.ST_Intersects(HexGrid.geom, func.ST_MakeEnvelope(*bounding_box, 4326))
        )
    return query.distinct().order_by(HexGrid.hex_id)


@cached(
    cache=LRUCache(maxsize=256), key=lambda _, *args, **kwargs: hashkey(*args, **kwargs)
)
def cached_geometries_hexgrid(
    db: Session, bounding_box: Optional[Tuple[float]] = None,
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
            AirQualityResultTable.point_id.label("point_id"),
            HexGrid.hex_id.label("hex_id"),
            AirQualityResultTable.measurement_start_utc.label("measurement_start_utc"),
            func.nullif(AirQualityResultTable.NO2_mean, "NaN").label("NO2_mean"),
            func.nullif(AirQualityResultTable.NO2_var, "NaN").label("NO2_var"),
            func.ST_AsText(func.ST_Transform(HexGrid.geom, 4326)).label("geom"),
        )
    else:
        query = db.query(
            AirQualityResultTable.point_id.label("point_id"),
            HexGrid.hex_id.label("hex_id"),
            AirQualityResultTable.measurement_start_utc.label("measurement_start_utc"),
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


@db_query()
def query_forecasts_hexgrid_hex_id(
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
            HexGrid.hex_id.label("hex_id"),
            AirQualityResultTable.measurement_start_utc.label("measurement_start_utc"),
            func.nullif(AirQualityResultTable.NO2_mean, "NaN").label("NO2_mean"),
            func.nullif(AirQualityResultTable.NO2_var, "NaN").label("NO2_var"),
            func.ST_AsText(func.ST_Transform(HexGrid.geom, 4326)).label("geom"),
        )
    else:
        query = db.query(
            HexGrid.hex_id.label("hex_id"),
            AirQualityResultTable.measurement_start_utc.label("measurement_start_utc"),
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
    cache=TTLCache(maxsize=256, ttl=2 * 60 * 60 * 24, timer=time),
    key=lambda _, *args, **kwargs: hashkey(*args, **kwargs),
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
    cache=TTLCache(maxsize=256, ttl=2 * 60 * 60 * 24, timer=time),
    key=lambda _, *args, **kwargs: hashkey(*args, **kwargs),
)
def cached_forecast_hexgrid_csv(
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
    query = query_forecasts_hexgrid_hex_id(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=with_geometry,
        bounding_box=bounding_box,
        output_type="df",
    )
    return query.round({"NO2_mean": 3, "NO2_var": 3}).to_csv(index=False)


# pylint: disable=C0103
@cached(
    cache=TTLCache(maxsize=256, ttl=2 * 60 * 60 * 24, timer=time),
    key=lambda _, *args, **kwargs: hashkey(*args, **kwargs),
)
def cached_forecast_hexgrid_small_csv(
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
    data = query_forecasts_hexgrid_hex_id(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=with_geometry,
        bounding_box=bounding_box,
        output_type="df",
    )

    data = data.round({"NO2_mean": 3, "NO2_var": 3})

    data["NO2"] = data[["NO2_mean", "NO2_var"]].apply(tuple, axis=1)

    return data.pivot(
        index="measurement_start_utc", columns="hex_id", values="NO2",
    ).to_csv()


@cached(
    cache=TTLCache(maxsize=256, ttl=2 * 60 * 60 * 24, timer=time),
    key=lambda _, instance_id, start_datetime, end_datetime, bounding_box: hashkey(
        instance_id, start_datetime, end_datetime, bounding_box
    ),
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
