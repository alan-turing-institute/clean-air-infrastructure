"""Air quality forecast API routes"""
import logging
from datetime import datetime, timedelta, date, timezone
from time import time
from typing import List, Tuple, Optional, cast, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...databases import get_db
from ...databases.queries.air_quality_forecast import (
    cached_instance_ids,
    cached_forecast_hexgrid_json,
    cached_forecast_hexgrid_geojson,
    cached_geometries_hexgrid,
    cached_instance_ids_on_run_date,
    cached_forecast_hexgrid_csv,
    cached_forecast_hexgrid_pivot_csv,
)
from ...databases.schemas.air_quality_forecast import (
    ForecastResultGeoJson,
    GeometryGeoJson,
    ForecastDatasetJson,
)
from ...responses import GeoJSONResponse, CSVResponse

router = APIRouter()
logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

# Define the bounding box for London
MIN_LONGITUDE = -0.510
MAX_LONGITUDE = 0.335
MIN_LATITUDE = 51.286
MAX_LATITUDE = 51.692


def bounding_box_params(
    lon_min: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, minimum longitude",
        example="-0.13",
        ge=MIN_LONGITUDE,
        le=MAX_LONGITUDE,
    ),
    lon_max: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, maximum longitude",
        example="-0.12",
        ge=MIN_LONGITUDE,
        le=MAX_LONGITUDE,
    ),
    lat_min: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, minimum latitude",
        example="51.525",
        ge=MIN_LATITUDE,
        le=MAX_LATITUDE,
    ),
    lat_max: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, maximum latitude",
        example="51.535",
        ge=MIN_LATITUDE,
        le=MAX_LATITUDE,
    ),
) -> Optional[Tuple[float, float, float, float]]:
    """Common parameters for defining a bounding box"""
    # Ensure that all bounding box parameters are set if any single one is
    if any([lon_min, lon_max, lat_min, lat_max]):
        # Longitude
        lon_min = lon_min if lon_min else MIN_LONGITUDE
        lon_max = lon_max if lon_max else MAX_LONGITUDE
        if lon_min >= lon_max:
            raise HTTPException(
                400,
                detail=f"Minimum longitude '{lon_min}' must be less than maximum '{lon_max}'",
            )
        # Latitude
        lat_min = lat_min if lat_min else MIN_LATITUDE
        lat_max = lat_max if lat_max else MAX_LATITUDE
        if lat_min >= lat_max:
            raise HTTPException(
                400,
                detail=f"Minimum latitude '{lon_min}' must be less than maximum '{lon_max}'",
            )
    # Return a bounding box if any bounding parameter was provided
    if all([lon_min, lat_min, lon_max, lat_max]):
        return (
            cast(float, lon_min),
            cast(float, lat_min),
            cast(float, lon_max),
            cast(float, lat_max),
        )
    return None


@router.get(
    "/forecast/hexgrid/geometries",
    description="Geometries for combining with plain JSON forecasts",
    response_class=GeoJSONResponse,
    response_model=GeometryGeoJson,
)
def forecast_hexgrid_geometries(
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> GeometryGeoJson:
    """Retrieve hexgrid geometries in JSON

    Returns:
        json: JSON containing geometry of each hexgrid point
    """
    request_start = time()

    # Get forecasts in this range (using a bounding box if specified)
    query_results = cached_geometries_hexgrid(db, bounding_box=bounding_box)

    # Return the query results as a GeoJSON FeatureCollection
    logger.info(
        "Processing hexgrid geometries request took %.2fs", time() - request_start
    )
    return query_results


@router.get(
    "/forecast/hexgrid/json",
    description="Most up-to-date hexgrid forecasts for a given hour in JSON",
    response_model=ForecastDatasetJson,
)
def forecast_hexgrid_1hr_json(
    time_: datetime = Query(
        None,
        alias="time",
        description="JSON forecasts for the hour containing this ISO-formatted time",
        example="2021-08-12T06:00",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> Dict:
    """Retrieve one hour of hexgrid forecasts containing the requested time in JSON

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        json: JSON containing one hour of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = time_.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids(db, start_datetime, end_datetime)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    # Get forecasts in this range (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_json(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=False,
        bounding_box=bounding_box,
    )
    # Return the query results as a list of tuples
    # This will be automatically converted to ForecastResultJson using from_orm
    logger.info("Processing hexgrid JSON request took %.2fs", time() - request_start)

    response = {
        "run_datetime": instance_run_date.replace(tzinfo=timezone.utc).strftime(
            "ran_%Y-%m-%d_%H:%M:%S"
        ),
        "data": [
            {
                "measurement_start_utc": measurement[0],
                "hex_id": measurement[1],
                "NO2_mean": measurement[2],
                "NO2_var": measurement[3],
            }
            for measurement in query_results
        ],
    }

    return response


@router.get(
    "/forecast/hexgrid/csv",
    description="Most up-to-date hexgrid forecasts for a given hour in CSV",
    response_class=CSVResponse,
)
def forecast_hexgrid_1hr_csv(
    time_: datetime = Query(
        None,
        alias="time",
        description="JSON forecasts for the hour containing this ISO-formatted time",
        example="2021-08-12T06:00",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> CSVResponse:
    """Retrieve one hour of hexgrid forecasts containing the requested time in CSV

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        csv: CSV containing one hour of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = time_.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids(db, start_datetime, end_datetime)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    # Get forecasts in this range (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_csv(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=False,
        run_datetime=instance_run_date,
        bounding_box=bounding_box,
    )
    # Return the query results as a list of tuples
    # This will be automatically converted to ForecastResultJson using from_orm
    logger.info("Processing hexgrid CSV request took %.2fs", time() - request_start)
    return CSVResponse(query_results)


@router.get(
    "/forecast/hexgrid/csv_pivot",
    description="Most up-to-date hexgrid forecasts for a given hour in CSV",
    response_class=CSVResponse,
)
def forecast_hexgrid_1hr_csv_pivot(
    time_: datetime = Query(
        None,
        alias="time",
        description="JSON forecasts for the hour containing this ISO-formatted time",
        example="2021-08-12T06:00",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> CSVResponse:
    """Retrieve one hour of hexgrid forecasts containing the requested time in CSV

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        csv: CSV containing one hour of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = time_.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids(db, start_datetime, end_datetime)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    # Get forecasts in this range (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_pivot_csv(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=False,
        run_datetime=instance_run_date,
        bounding_box=bounding_box,
    )
    # Return the query results as a list of tuples
    # This will be automatically converted to ForecastResultJson using from_orm
    logger.info("Processing hexgrid CSV request took %.2fs", time() - request_start)
    return CSVResponse(query_results)


@router.get(
    "/forecast/hexgrid/geojson",
    description="Most up-to-date forecasts for a given hour in GeoJSON",
    response_class=GeoJSONResponse,
    response_model=ForecastResultGeoJson,
)
def forecast_hexgrid_1hr_geojson(
    time_: datetime = Query(
        None,
        alias="time",
        description="GeoJSON forecasts for the hour containing this ISO-formatted time",
        example="2021-08-12T06:00",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> Optional[ForecastResultGeoJson]:
    """Retrieve one hour of hexgrid forecasts containing the requested time in GeoJSON

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        ForecastResultGeoJson: GeoJSON containing one hour of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = time_.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids(db, start_datetime, end_datetime)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        print("No forecasts cover this period!")
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    # Get forecasts in this range as a GeoJSON FeatureCollection (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_geojson(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        run_datetime=instance_run_date,
        bounding_box=bounding_box,
    )

    # Return the query results as a GeoJSON FeatureCollection
    logger.info("Processing hexgrid GeoJSON request took %.2fs", time() - request_start)
    return query_results


@router.get(
    "/forecast/hexgrid/json/48hr",
    description="Most up-to-date hexgrid forecasts for a given two days in JSON",
    response_model=List[ForecastDatasetJson],
)
def forecast_hexgrid__48hr_json(
    run_date: date = Query(
        None,
        alias="date",
        description="JSON forecasts for the two days starting on this date",
        example="2021-08-12",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> Dict:
    """Retrieve 48hrs of hexgrid forecasts in JSON

    Args:
        run_date (datetime): First day of the 48hr period to get data for

    Returns:
        json: JSON containing one hour of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = datetime.combine(run_date, datetime.min.time())
    end_datetime = start_datetime + timedelta(days=2)

    logger.info("Getting instance ids")

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids_on_run_date(db, run_date)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    logger.info("Instance found: %s", instance_id)
    logger.info(
        "Getting data from %s between %s and %s",
        instance_id,
        start_datetime,
        start_datetime,
    )

    # Get forecasts in this range (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_json(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=False,
        bounding_box=bounding_box,
    )
    # Return the query results as a list of tuples
    # This will be automatically converted to ForecastResultJson using from_orm
    logger.info("Processing hexgrid JSON request took %.2fs", time() - request_start)

    response = {
        "run_datetime": instance_run_date.replace(tzinfo=timezone.utc).strftime(
            "ran_%Y-%m-%d_%H:%M:%S"
        ),
        "data": [
            {
                "measurement_start_utc": measurement[0],
                "hex_id": measurement[1],
                "NO2_mean": measurement[2],
                "NO2_var": measurement[3],
            }
            for measurement in query_results
        ],
    }

    return response


@router.get(
    "/forecast/hexgrid/geojson/48hr",
    description="Hexgrid forecasts for a given two days in GEOJSON",
    response_class=GeoJSONResponse,
    response_model=ForecastResultGeoJson,
)
def forecast_hexgrid__48hr_geojson(
    run_date: date = Query(
        None,
        alias="date",
        description="JSON forecasts for the two days starting on this date",
        example="2021-08-12",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> Optional[ForecastResultGeoJson]:
    """Retrieve 48hrs of hexgrid forecasts in GEOJSON

    Args:
        run_date (datetime): First day of the 48hr period to get data for

    Returns:
        geojson: GEOJSON containing one hour of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = datetime.combine(run_date, datetime.min.time())
    end_datetime = start_datetime + timedelta(days=2)

    logger.info("Getting instance ids")

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids_on_run_date(db, run_date)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    logger.info("Instance found: %s", instance_id)
    logger.info(
        "Getting data from %s between %s and %s",
        instance_id,
        start_datetime,
        start_datetime,
    )

    # Get forecasts in this range as a GeoJSON FeatureCollection (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_geojson(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        run_datetime=instance_run_date,
        bounding_box=bounding_box,
    )

    # Return the query results as a GeoJSON FeatureCollection
    logger.info("Processing hexgrid GeoJSON request took %.2fs", time() - request_start)
    return query_results


@router.get(
    "/forecast/hexgrid/csv/48hr",
    description="Most up-to-date hexgrid forecasts for a given two days in JSON",
    response_class=CSVResponse,
)
def forecast_hexgrid_48hr_csv(
    run_date: date = Query(
        None,
        alias="date",
        description="JSON forecasts for the two days starting on this date",
        example="2021-08-12",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> Optional[CSVResponse]:
    """Retrieve 48hrs of hexgrid forecasts in CSV

    Args:
        run_date (datetime): First day of the 48hr period to get data for

    Returns:
        json: CSV containing 48 hours of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = datetime.combine(run_date, datetime.min.time())
    end_datetime = start_datetime + timedelta(days=2)

    logger.info("Getting instance ids")

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids_on_run_date(db, run_date)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    logger.info("Instance found: %s", instance_id)
    logger.info(
        "Getting data from %s between %s and %s",
        instance_id,
        start_datetime,
        start_datetime,
    )

    # Get forecasts in this range (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_csv(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=False,
        run_datetime=instance_run_date,
        bounding_box=bounding_box,
    )
    # Return the query results as a list of tuples
    # This will be automatically converted to ForecastResultJson using from_orm
    logger.info("Processing hexgrid CSV request took %.2fs", time() - request_start)
    return CSVResponse(query_results)


@router.get(
    "/forecast/hexgrid/csv_pivot/48hr",
    description="Most up-to-date hexgrid forecasts for a given two days in CSV",
    response_class=CSVResponse,
)
def forecast_hexgrid_48hr_csv_pivot(
    run_date: date = Query(
        None,
        alias="date",
        description="Forecasts for the two days starting on this date",
        example="2021-08-12",
    ),
    index: int = 0,
    db: Session = Depends(get_db),
    bounding_box: Tuple[float] = Depends(bounding_box_params),
) -> CSVResponse:
    """Retrieve 48hrs of hexgrid forecasts in CSV

    Args:
        run_date (datetime): First day of the 48hr period to get data for

    Returns:
        json: CSV containing 48 hours of forecasts at each hexgrid point
    """
    request_start = time()

    # Establish start and end datetimes
    start_datetime = datetime.combine(run_date, datetime.min.time())
    end_datetime = start_datetime + timedelta(days=2)

    logger.info("Getting instance ids")

    # Get the most recent instance ID among those which predict in the required interval
    instance_ids = cached_instance_ids_on_run_date(db, run_date)
    if index < len(instance_ids):
        instance_id, instance_run_date = instance_ids[index]
    else:
        raise HTTPException(status_code=404, detail="No forecasts cover this period")

    logger.info("Instance found: %s", instance_id)
    logger.info(
        "Getting data from %s between %s and %s",
        instance_id,
        start_datetime,
        start_datetime,
    )

    # Get forecasts in this range (using a bounding box if specified)
    query_results = cached_forecast_hexgrid_pivot_csv(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        with_geometry=False,
        run_datetime=instance_run_date,
        bounding_box=bounding_box,
    )
    # Return the query results as a list of tuples
    # This will be automatically converted to ForecastResultJson using from_orm
    logger.info("Processing hexgrid CSV request took %.2fs", time() - request_start)
    return CSVResponse(query_results)
